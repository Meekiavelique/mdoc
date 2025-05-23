import pymysql
import sqlite3
import os
from datetime import datetime
from api.config import DATABASE_CONFIG

class AnalyticsDB:
    def __init__(self):
        self.config = DATABASE_CONFIG
        self.init_db()
    
    def get_connection(self):
        if self.config['type'] == 'mysql':
            return pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4'
            )
        else:
            db_path = self.config.get('path', os.path.join(os.path.dirname(__file__), '..', 'data', 'analytics.db'))
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return sqlite3.connect(db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.config['type'] == 'mysql':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_name VARCHAR(255) NOT NULL,
                    view_count INT DEFAULT 0,
                    last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_document_name (document_name)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS view_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_name VARCHAR(255) NOT NULL,
                    ip_hash VARCHAR(64),
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_document_name (document_name),
                    INDEX idx_timestamp (timestamp)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_name TEXT NOT NULL,
                    view_count INTEGER DEFAULT 0,
                    last_viewed TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS view_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_name TEXT NOT NULL,
                    ip_hash TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        conn.commit()
        conn.close()
    
    def record_view(self, document_name, ip_hash=None, user_agent=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.config['type'] == 'mysql':
            cursor.execute('''
                INSERT INTO page_views (document_name, view_count, last_viewed)
                VALUES (%s, 1, NOW())
                ON DUPLICATE KEY UPDATE 
                view_count = view_count + 1, 
                last_viewed = NOW()
            ''', (document_name,))
            
            cursor.execute('''
                INSERT INTO view_logs (document_name, ip_hash, user_agent)
                VALUES (%s, %s, %s)
            ''', (document_name, ip_hash, user_agent))
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO page_views (document_name, view_count, last_viewed)
                VALUES (?, 0, ?)
            ''', (document_name, datetime.now()))
            
            cursor.execute('''
                UPDATE page_views 
                SET view_count = view_count + 1, last_viewed = ?
                WHERE document_name = ?
            ''', (datetime.now(), document_name))
            
            cursor.execute('''
                INSERT INTO view_logs (document_name, ip_hash, user_agent)
                VALUES (?, ?, ?)
            ''', (document_name, ip_hash, user_agent))
        
        conn.commit()
        conn.close()
    
    def get_view_count(self, document_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.config['type'] == 'mysql':
            cursor.execute('SELECT view_count FROM page_views WHERE document_name = %s', (document_name,))
        else:
            cursor.execute('SELECT view_count FROM page_views WHERE document_name = ?', (document_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def get_popular_documents(self, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.config['type'] == 'mysql':
            cursor.execute('''
                SELECT document_name, view_count, last_viewed
                FROM page_views
                ORDER BY view_count DESC
                LIMIT %s
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT document_name, view_count, last_viewed
                FROM page_views
                ORDER BY view_count DESC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'name': row[0], 'views': row[1], 'last_viewed': row[2]} for row in results]

analytics_db = AnalyticsDB()