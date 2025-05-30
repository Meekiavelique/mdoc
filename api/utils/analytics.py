import psycopg2
import psycopg2.extras
import sqlite3
import os
from datetime import datetime, timedelta
from api.config import DATABASE_CONFIG
import threading
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class AnalyticsDB:
    def __init__(self):
        self.config = DATABASE_CONFIG.copy()
        self._lock = threading.Lock()
        self._initialized = False
        self._connection_pool = {}
        self._vercel_mode = os.environ.get('VERCEL') == '1'
        self._graceful_degradation = True
        
    def is_vercel_environment(self):
        return self._vercel_mode or os.environ.get('VERCEL_ENV') is not None
        
    def get_connection(self):
        thread_id = threading.get_ident()
        
        if thread_id in self._connection_pool:
            try:
                conn = self._connection_pool[thread_id]
                if self.config['type'] in ['postgres', 'postgresql']:
                    with conn.cursor() as cursor:
                        cursor.execute('SELECT 1')
                    return conn
                elif self.config['type'] == 'mysql':
                    conn.ping(reconnect=True)
                    return conn
                else:
                    conn.execute('SELECT 1')
                    return conn
            except:
                if thread_id in self._connection_pool:
                    del self._connection_pool[thread_id]
        
        database_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
        
        if database_url:
            try:
                parsed = urlparse(database_url)
                
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path[1:],
                    sslmode='require',
                    connect_timeout=10
                )
                conn.autocommit = False
                logger.info(f"PostgreSQL connection successful to {parsed.hostname}")
                self._connection_pool[thread_id] = conn
                self.config['type'] = 'postgres'
                return conn
            except Exception as e:
                logger.error(f"PostgreSQL connection failed: {e}")
        
        if self.config['type'] in ['postgres', 'postgresql']:
            try:
                conn = psycopg2.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    user=self.config['username'],
                    password=self.config['password'],
                    database=self.config['database'],
                    sslmode='require',
                    connect_timeout=10
                )
                conn.autocommit = False
                logger.info(f"PostgreSQL connection successful to {self.config['host']}")
                self._connection_pool[thread_id] = conn
                return conn
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}")
                if self.is_vercel_environment():
                    logger.warning("Running on Vercel without external database - analytics disabled")
                    return None
        
        if not self.is_vercel_environment():
            try:
                db_path = self.config.get('path', os.path.join(os.path.dirname(__file__), '..', 'data', 'analytics.db'))
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                conn = sqlite3.connect(
                    db_path, 
                    timeout=30.0, 
                    check_same_thread=False,
                    isolation_level=None
                )
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=10000')
                conn.execute('PRAGMA temp_store=memory')
                
                self._connection_pool[thread_id] = conn
                self.config['type'] = 'sqlite'
                return conn
            except Exception as e:
                logger.error(f"SQLite connection failed: {e}")
                
        return None
    
    def init_db(self):
        if self._initialized:
            return True
        
        if self.is_vercel_environment() and not os.environ.get('POSTGRES_URL') and not os.environ.get('DATABASE_URL'):
            logger.warning("Analytics disabled on Vercel - no external database configured")
            self._initialized = True
            self._graceful_degradation = True
            return True
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Database initialization attempt {attempt + 1}/{max_retries}")
                conn = self.get_connection()
                
                if conn is None:
                    logger.warning("No database connection available - analytics disabled")
                    self._initialized = True
                    self._graceful_degradation = True
                    return True
                
                cursor = conn.cursor()
                
                if self.config['type'] in ['postgres', 'postgresql']:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS page_views (
                            id SERIAL PRIMARY KEY,
                            document_name VARCHAR(255) NOT NULL UNIQUE,
                            view_count INTEGER DEFAULT 0,
                            last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_view_count ON page_views(view_count DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_last_viewed ON page_views(last_viewed DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_document_name ON page_views(document_name)
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS view_logs (
                            id SERIAL PRIMARY KEY,
                            document_name VARCHAR(255) NOT NULL,
                            ip_hash VARCHAR(64),
                            user_agent TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_log_doc_name ON view_logs(document_name)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_log_timestamp ON view_logs(timestamp DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_log_ip_time ON view_logs(ip_hash, timestamp)
                    ''')
                    
                    conn.commit()
                    
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS page_views (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            document_name TEXT NOT NULL UNIQUE,
                            view_count INTEGER DEFAULT 0,
                            last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_view_count ON page_views(view_count DESC)''')
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_last_viewed ON page_views(last_viewed DESC)''')
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_document_name ON page_views(document_name)''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS view_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            document_name TEXT NOT NULL,
                            ip_hash TEXT,
                            user_agent TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_log_doc_name ON view_logs(document_name)''')
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_log_timestamp ON view_logs(timestamp DESC)''')
                    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_log_ip_time ON view_logs(ip_hash, timestamp)''')
                
                cursor.execute('SELECT COUNT(*) FROM page_views')
                count = cursor.fetchone()[0]
                logger.info(f"Database initialized successfully using {self.config['type']}, current documents: {count}")
                self._initialized = True
                self._graceful_degradation = False
                return True
                
            except Exception as e:
                logger.error(f"Database initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.warning("Failed to initialize database - analytics will be disabled")
                    self._initialized = True
                    self._graceful_degradation = True
                    return True
                time.sleep(min(2 ** attempt, 5))
        
        return True
    
    def record_view(self, document_name, ip_hash=None, user_agent=None):
        if not self._initialized or self._graceful_degradation:
            logger.debug("Analytics disabled - not recording view")
            return 0
        
        if not document_name or not document_name.strip():
            logger.warning("Empty document name provided")
            return 0
            
        with self._lock:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    conn = self.get_connection()
                    if conn is None:
                        return 0
                        
                    cursor = conn.cursor()
                    
                    if self.config['type'] in ['postgres', 'postgresql']:
                        cursor.execute('''
                            INSERT INTO page_views (document_name, view_count, last_viewed, created_at)
                            VALUES (%s, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (document_name) 
                            DO UPDATE SET 
                                view_count = page_views.view_count + 1, 
                                last_viewed = CURRENT_TIMESTAMP
                            RETURNING view_count
                        ''', (document_name,))
                        
                        result = cursor.fetchone()
                        view_count = result[0] if result else 1
                        
                        cursor.execute('''
                            INSERT INTO view_logs (document_name, ip_hash, user_agent, timestamp)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        ''', (document_name, ip_hash, user_agent))
                        
                        conn.commit()
                        
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
                        
                        view_count = new_count
                    
                    logger.info(f"View recorded for {document_name}: {view_count}")
                    return view_count
                    
                except Exception as e:
                    logger.error(f"Error recording view for {document_name} (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to record view for {document_name} after all retries")
                        return 0
                    time.sleep(0.1 * (attempt + 1))
            
            return 0
    
    def get_view_count(self, document_name):
        if not self._initialized or self._graceful_degradation:
            return 0
        
        if not document_name or not document_name.strip():
            return 0
            
        max_retries = 2
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                if conn is None:
                    return 0
                    
                cursor = conn.cursor()
                
                if self.config['type'] in ['postgres', 'postgresql']:
                    cursor.execute('SELECT view_count FROM page_views WHERE document_name = %s', (document_name,))
                else:
                    cursor.execute('SELECT view_count FROM page_views WHERE document_name = ?', (document_name,))
                
                result = cursor.fetchone()
                count = result[0] if result else 0
                
                logger.debug(f"Retrieved view count for {document_name}: {count}")
                return count
                
            except Exception as e:
                logger.error(f"Error getting view count for {document_name} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return 0
                time.sleep(0.1 * (attempt + 1))
        
        return 0
    
    def get_popular_documents(self, limit=10):
        if not self._initialized or self._graceful_degradation:
            return []
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                if conn is None:
                    return []
                    
                cursor = conn.cursor()
                
                if self.config['type'] in ['postgres', 'postgresql']:
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
                popular_docs = [{'name': row[0], 'views': row[1], 'last_viewed': row[2]} for row in results]
                
                logger.debug(f"Retrieved {len(popular_docs)} popular documents")
                return popular_docs
                
            except Exception as e:
                logger.error(f"Error getting popular documents (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return []
                time.sleep(0.1 * (attempt + 1))
        
        return []
    
    def __del__(self):
        try:
            for conn in self._connection_pool.values():
                if conn:
                    conn.close()
        except:
            pass

analytics_db = AnalyticsDB()