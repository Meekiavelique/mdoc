import os
import requests
from datetime import datetime, timedelta
import functools
import json
from api.config import GITHUB_REPO

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'github_cache.json')
CACHE_DURATION = timedelta(hours=6)

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            for key in list(cache.keys()):
                if datetime.fromisoformat(cache[key]['timestamp']) < datetime.now() - CACHE_DURATION:
                    del cache[key]
            return cache
    except:
        return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except:
        pass

def get_github_file_history(file_path, repo=GITHUB_REPO):
    cache = load_cache()
    cache_key = f"{repo}:{file_path}"
    
    if cache_key in cache:
        return cache[cache_key]['data']
    
    api_url = f"https://api.github.com/repos/{repo}/commits"
    params = {"path": file_path, "per_page": 50}
    
    headers = {}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 403:
            if cache_key in cache:
                return cache[cache_key]['data']
            return []
        
        response.raise_for_status()
        
        commits = response.json()
        history = []
        
        for commit in commits[:20]:
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
        
        cache[cache_key] = {
            'data': history,
            'timestamp': datetime.now().isoformat()
        }
        save_cache(cache)
        return history
        
    except Exception as e:
        if cache_key in cache:
            return cache[cache_key]['data']
        return []

def get_file_at_commit(file_path, commit_hash, repo=GITHUB_REPO):
    cache = load_cache()
    cache_key = f"{repo}:{file_path}:{commit_hash}"
    
    if cache_key in cache:
        return cache[cache_key]['data']
    
    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    params = {"ref": commit_hash}
    
    headers = {"Accept": "application/vnd.github.v3.raw"}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        if response.status_code == 403:
            return None
        response.raise_for_status()
        
        content = response.text
        cache[cache_key] = {
            'data': content,
            'timestamp': datetime.now().isoformat()
        }
        save_cache(cache)
        return content
    except:
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