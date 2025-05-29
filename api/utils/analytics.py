import pymysql
import sqlite3
import os
from datetime import datetime, timedelta
from api.config import DATABASE_CONFIG
import threading
import time

class AnalyticsDB:
    def __init__(self):
        self.config = DATABASE_CONFIG
        self._lock = threading.Lock()
        self._initialized = False
        self.init_db()
    
    def get_connection(self):
        if self.config['type'] == 'mysql':
            try:
                conn = pymysql.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    user=self.config['username'],
                    password=self.config['password'],
                    database=self.config['database'],
                    charset='utf8mb4',
                    autocommit=False,
                    connect_timeout=10
                )
                print(f"MySQL connection successful to {self.config['host']}")
                return conn
            except Exception as e:
                print(f"MySQL connection failed: {e}")
                print("Falling back to SQLite")
                self.config['type'] = 'sqlite'
        
        db_path = self.config.get('path', os.path.join(os.path.dirname(__file__), '..', 'data', 'analytics.db'))
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL')
        return conn
    
    def init_db(self):
        if self._initialized:
            return
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
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
                            UNIQUE KEY unique_doc (document_name),
                            INDEX idx_view_count (view_count DESC),
                            INDEX idx_last_viewed (last_viewed DESC)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS view_logs (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            document_name VARCHAR(255) NOT NULL,
                            ip_hash VARCHAR(64),
                            user_agent TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_document_name (document_name),
                            INDEX idx_timestamp (timestamp DESC)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    ''')
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS page_views (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            document_name TEXT NOT NULL UNIQUE,
                            view_count INTEGER DEFAULT 0,
                            last_viewed TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_view_count ON page_views(view_count DESC)''')
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_last_viewed ON page_views(last_viewed DESC)''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS view_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            document_name TEXT NOT NULL,
                            ip_hash TEXT,
                            user_agent TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_doc_name ON view_logs(document_name)''')
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_timestamp ON view_logs(timestamp DESC)''')
                
                conn.commit()
                conn.close()
                self._initialized = True
                print(f"Database initialized successfully using {self.config['type']}")
                break
                
            except Exception as e:
                print(f"Database initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print("Failed to initialize database after all retries")
                    return
                time.sleep(1)
    
    def record_view(self, document_name, ip_hash=None, user_agent=None):
        if not self._initialized:
            print("Database not initialized, cannot record view")
            return 0
            
        with self._lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                if self.config['type'] == 'mysql':
                    cursor.execute('''
                        INSERT INTO page_views (document_name, view_count, last_viewed, created_at)
                        VALUES (%s, 1, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE 
                        view_count = view_count + 1, 
                        last_viewed = NOW()
                    ''', (document_name,))
                    
                    cursor.execute('SELECT view_count FROM page_views WHERE document_name = %s', (document_name,))
                    result = cursor.fetchone()
                    view_count = result[0] if result else 1
                    
                    cursor.execute('''
                        INSERT INTO view_logs (document_name, ip_hash, user_agent, timestamp)
                        VALUES (%s, %s, %s, NOW())
                    ''', (document_name, ip_hash, user_agent))
                    
                    conn.commit()
                    print(f"MySQL: View recorded for {document_name}: {view_count}")
                else:
                    cursor.execute('SELECT view_count FROM page_views WHERE document_name = ?', (document_name,))
                    result = cursor.fetchone()
                    current_count = result[0] if result else 0
                    new_count = current_count + 1
                    
                    if current_count == 0:
                        cursor.execute('''
                            INSERT INTO page_views (document_name, view_count, last_viewed, created_at)
                            VALUES (?, ?, ?, ?)
                        ''', (document_name, new_count, datetime.now().isoformat(), datetime.now().isoformat()))
                    else:
                        cursor.execute('''
                            UPDATE page_views 
                            SET view_count = ?, last_viewed = ?
                            WHERE document_name = ?
                        ''', (new_count, datetime.now().isoformat(), document_name))
                    
                    cursor.execute('''
                        INSERT INTO view_logs (document_name, ip_hash, user_agent, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (document_name, ip_hash, user_agent, datetime.now().isoformat()))
                    
                    conn.commit()
                    view_count = new_count
                    print(f"SQLite: View recorded for {document_name}: {view_count}")
                
                conn.close()
                return view_count
                
            except Exception as e:
                print(f"Error recording view for {document_name}: {e}")
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
                return 0
    
    def get_view_count(self, document_name):
        if not self._initialized:
            return 0
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.config['type'] == 'mysql':
                cursor.execute('SELECT view_count FROM page_views WHERE document_name = %s', (document_name,))
            else:
                cursor.execute('SELECT view_count FROM page_views WHERE document_name = ?', (document_name,))
            
            result = cursor.fetchone()
            count = result[0] if result else 0
            conn.close()
            
            print(f"Retrieved view count for {document_name}: {count} from {self.config['type']}")
            return count
            
        except Exception as e:
            print(f"Error getting view count for {document_name}: {e}")
            try:
                conn.close()
            except:
                pass
            return 0
    
    def get_popular_documents(self, limit=10):
        if not self._initialized:
            return []
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.config['type'] == 'mysql':
                cursor.execute('''
                    SELECT document_name, view_count, last_viewed
                    FROM page_views
                    WHERE view_count > 0
                    ORDER BY view_count DESC
                    LIMIT %s
                ''', (limit,))
            else:
                cursor.execute('''
                    SELECT document_name, view_count, last_viewed
                    FROM page_views
                    WHERE view_count > 0
                    ORDER BY view_count DESC
                    LIMIT ?
                ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [{'name': row[0], 'views': row[1], 'last_viewed': row[2]} for row in results]
            
        except Exception as e:
            print(f"Error getting popular documents: {e}")
            try:
                conn.close()
            except:
                pass
            return []
    
    def get_analytics_summary(self):
        if not self._initialized:
            return {'total_views': 0, 'total_documents': 0, 'unique_visitors': 0}
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.config['type'] == 'mysql':
                cursor.execute('SELECT SUM(view_count), COUNT(*) FROM page_views WHERE view_count > 0')
                total_views, total_docs = cursor.fetchone() or (0, 0)
                
                cursor.execute('SELECT COUNT(DISTINCT ip_hash) FROM view_logs WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)')
                unique_visitors = cursor.fetchone()[0] or 0
            else:
                cursor.execute('SELECT SUM(view_count), COUNT(*) FROM page_views WHERE view_count > 0')
                total_views, total_docs = cursor.fetchone() or (0, 0)
                
                cursor.execute('SELECT COUNT(DISTINCT ip_hash) FROM view_logs WHERE timestamp >= datetime("now", "-30 days")')
                unique_visitors = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_views': total_views or 0,
                'total_documents': total_docs or 0,
                'unique_visitors': unique_visitors or 0
            }
            
        except Exception as e:
            print(f"Error getting analytics summary: {e}")
            try:
                conn.close()
            except:
                pass
            return {'total_views': 0, 'total_documents': 0, 'unique_visitors': 0}

analytics_db = AnalyticsDB()