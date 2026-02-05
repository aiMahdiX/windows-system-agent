"""
State Manager - Manages conversation state and metrics with SQLite
Handles conversation history, user metrics, and system state persistence
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateManager:
    """Manages conversation state, history, and metrics using SQLite"""
    
    def __init__(self, db_path: str = "state.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT NOT NULL,
                    model_response TEXT,
                    model_used TEXT,
                    function_called TEXT,
                    function_params TEXT,
                    execution_status TEXT,
                    execution_time_ms REAL,
                    error_message TEXT
                )
            """)
            
            # Tool call history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    function_name TEXT NOT NULL,
                    params TEXT,
                    status TEXT,
                    result TEXT,
                    error TEXT,
                    execution_time_ms REAL,
                    attempts INTEGER
                )
            """)
            
            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    tags TEXT
                )
            """)
            
            # Session management table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    # ============ Conversation Methods ============
    
    def add_conversation(
        self,
        user_input: str,
        model_response: Optional[str] = None,
        model_used: Optional[str] = None,
        function_called: Optional[str] = None,
        function_params: Optional[Dict] = None,
        execution_status: Optional[str] = None,
        execution_time_ms: float = 0.0,
        error_message: Optional[str] = None
    ) -> int:
        """Add conversation entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation (
                    user_input, model_response, model_used,
                    function_called, function_params,
                    execution_status, execution_time_ms, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_input,
                model_response,
                model_used,
                function_called,
                json.dumps(function_params) if function_params else None,
                execution_status,
                execution_time_ms,
                error_message
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_conversation_history(
        self,
        limit: int = 50,
        offset: int = 0,
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM conversation"
            params = []
            
            if model:
                query += " WHERE model_used = ?"
                params.append(model)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_conversations(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations by keyword"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversation
                WHERE user_input LIKE ? OR model_response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_old_conversations(self, days: int = 30):
        """Delete conversations older than N days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute(
                "DELETE FROM conversation WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            conn.commit()
            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} old conversations")
    
    # ============ Tool Call Methods ============
    
    def add_tool_call(
        self,
        function_name: str,
        params: Optional[Dict] = None,
        status: str = "pending",
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0.0,
        attempts: int = 1
    ) -> int:
        """Record tool call execution"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tool_calls (
                    function_name, params, status, result, error,
                    execution_time_ms, attempts
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                function_name,
                json.dumps(params) if params else None,
                status,
                json.dumps(result) if result else None,
                error,
                execution_time_ms,
                attempts
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_tool_calls(
        self,
        function_name: Optional[str] = None,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tool call history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM tool_calls WHERE 1=1"
            params = []
            
            if function_name:
                query += " AND function_name = ?"
                params.append(function_name)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict["params"]:
                    row_dict["params"] = json.loads(row_dict["params"])
                if row_dict["result"]:
                    row_dict["result"] = json.loads(row_dict["result"])
                results.append(row_dict)
            
            return results
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get tool call statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total calls
            cursor.execute("SELECT COUNT(*) FROM tool_calls")
            total = cursor.fetchone()[0]
            
            # By status
            cursor.execute("""
                SELECT status, COUNT(*) FROM tool_calls
                GROUP BY status
            """)
            by_status = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM tool_calls WHERE status = 'success'")
            successful = cursor.fetchone()[0]
            
            # Average execution time
            cursor.execute("SELECT AVG(execution_time_ms) FROM tool_calls")
            avg_time = cursor.fetchone()[0] or 0
            
            # Most used functions
            cursor.execute("""
                SELECT function_name, COUNT(*) FROM tool_calls
                GROUP BY function_name
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)
            most_used = [(row[0], row[1]) for row in cursor.fetchall()]
            
            return {
                "total_calls": total,
                "by_status": by_status,
                "success_rate": successful / total if total > 0 else 0,
                "avg_execution_time_ms": avg_time,
                "most_used_functions": most_used
            }
    
    # ============ Preference Methods ============
    
    def set_preference(self, key: str, value: Any):
        """Set user preference"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            value_str = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute("""
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str))
            conn.commit()
            logger.info(f"Preference saved: {key} = {value}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return row[0]
            return default
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM preferences")
            
            result = {}
            for row in cursor.fetchall():
                try:
                    result[row[0]] = json.loads(row[1])
                except json.JSONDecodeError:
                    result[row[0]] = row[1]
            
            return result
    
    # ============ Metric Methods ============
    
    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record system metric"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (metric_name, metric_value, tags)
                VALUES (?, ?, ?)
            """, (
                metric_name,
                metric_value,
                json.dumps(tags) if tags else None
            ))
            conn.commit()
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metrics from last N hours"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            query = "SELECT * FROM metrics WHERE timestamp > ?"
            params = [cutoff_time.isoformat()]
            
            if metric_name:
                query += " AND metric_name = ?"
                params.append(metric_name)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict["tags"]:
                    row_dict["tags"] = json.loads(row_dict["tags"])
                results.append(row_dict)
            
            return results
    
    # ============ Session Methods ============
    
    def create_session(
        self,
        session_name: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """Create new session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO sessions (session_name, metadata, is_active)
                    VALUES (?, ?, 1)
                """, (
                    session_name,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                logger.info(f"Session created: {session_name}")
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.warning(f"Session already exists: {session_name}")
                return None
    
    def list_sessions(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List sessions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM sessions"
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
            
            query += " ORDER BY last_accessed DESC"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                if row_dict["metadata"]:
                    row_dict["metadata"] = json.loads(row_dict["metadata"])
                results.append(row_dict)
            
            return results
    
    def delete_session(self, session_name: str):
        """Delete session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM sessions WHERE session_name = ?",
                (session_name,)
            )
            conn.commit()
            logger.info(f"Session deleted: {session_name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversation count
            cursor.execute("SELECT COUNT(*) FROM conversation")
            conversations = cursor.fetchone()[0]
            
            # Tool calls count
            cursor.execute("SELECT COUNT(*) FROM tool_calls")
            tool_calls = cursor.fetchone()[0]
            
            # Models used
            cursor.execute("""
                SELECT model_used, COUNT(*) FROM conversation
                WHERE model_used IS NOT NULL
                GROUP BY model_used
            """)
            models = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average response time
            cursor.execute("SELECT AVG(execution_time_ms) FROM conversation")
            avg_response_time = cursor.fetchone()[0] or 0
            
            return {
                "total_conversations": conversations,
                "total_tool_calls": tool_calls,
                "models_used": models,
                "avg_response_time_ms": avg_response_time
            }
    
    def export_data(self, export_path: str = "export.json"):
        """Export all data to JSON"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "conversations": self.get_conversation_history(limit=10000),
            "tool_calls": self.get_tool_calls(limit=10000),
            "preferences": self.get_all_preferences(),
            "sessions": self.list_sessions(active_only=False),
            "statistics": self.get_statistics()
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Data exported to {export_path}")
        return export_path
    
    def clear_all_data(self, confirm: bool = False):
        """Clear all data (requires confirmation)"""
        if not confirm:
            logger.warning("Confirmation required to clear data")
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation")
            cursor.execute("DELETE FROM tool_calls")
            cursor.execute("DELETE FROM preferences")
            cursor.execute("DELETE FROM metrics")
            cursor.execute("DELETE FROM sessions")
            conn.commit()
            logger.warning("All data cleared")
            return True
