import os
import requests
from datetime import datetime, timedelta
import functools
from api.config import GITHUB_REPO

@functools.lru_cache(maxsize=32)
def get_github_file_history(file_path, repo=GITHUB_REPO):
    api_url = f"https://api.github.com/repos/{repo}/commits"
    params = {"path": file_path, "per_page": 100}
    
    headers = {}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        
        commits = response.json()
        history = []
        
        for commit in commits:
            commit_data = {
                "hash": commit["sha"],
                "short_hash": commit["sha"][:7],
                "author": commit["commit"]["author"]["name"],
                "author_username": commit.get("author", {}).get("login", ""),
                "date": datetime.strptime(
                    commit["commit"]["author"]["date"], 
                    "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%Y-%m-%d %H:%M"),
                "message": commit["commit"]["message"].split("\n")[0],
                "url": commit["html_url"]
            }
            history.append(commit_data)
            
        return history
    except Exception as e:
        print(f"Error fetching GitHub history: {str(e)}")
        return []

def get_file_at_commit(file_path, commit_hash, repo=GITHUB_REPO):
    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    params = {"ref": commit_hash}
    
    headers = {"Accept": "application/vnd.github.v3.raw"}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching file at commit: {str(e)}")
        return None

@functools.lru_cache(maxsize=32)
def get_template_history(template_name):
    md_history = get_github_file_history(f"api/templates/docs/{template_name}.md")
    html_history = get_github_file_history(f"api/templates/docs/{template_name}.html")
    
    combined_history = md_history + html_history
    return sorted(
        combined_history, 
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"), 
        reverse=True
    )

def get_document_contributors(template_name):
    history = get_template_history(template_name)
    contributors = {}
    
    for commit in history:
        username = commit.get("author_username", "")
        if username and username not in contributors:
            contributors[username] = {
                "username": username,
                "name": commit["author"],
                "last_commit": commit["date"]
            }
    
    return list(contributors.values())

def get_document_author(template_name):
    history = get_template_history(template_name)
    if history:
        return history[-1].get("author_username", "")
    return ""

def get_last_updated(template_name):
    history = get_template_history(template_name)
    if history:
        last_update = datetime.strptime(history[0]["date"], "%Y-%m-%d %H:%M")
        now = datetime.now()
        diff = now - last_update
        
        if diff.days == 0:
            return "Today"
        elif diff.days == 1:
            return "1 day ago"
        elif diff.days <= 7:
            return f"{diff.days} days ago"
        elif diff.days <= 14:
            return "1 week ago"
        else:
            return None
    return None

def is_recently_updated(template_name):
    last_updated = get_last_updated(template_name)
    return last_updated is not None