import sqlite3
import datetime
from typing import List, Dict, Any, Optional

OBS_DB_PATH = "observability.db"

def init_observability_db():
    with sqlite3.connect(OBS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                timestamp TEXT,
                user_query TEXT,
                generated_sql TEXT,
                retrieved_context TEXT,
                final_response TEXT,
                execution_time_ms REAL,
                status TEXT,
                hallucination_flag BOOLEAN,
                faithfulness_score REAL
            )
        """)
        conn.commit()

def log_trace(
    trace_id: str,
    user_query: str,
    generated_sql: str,
    retrieved_context: str,
    final_response: str,
    execution_time_ms: float,
    status: str,
    hallucination_flag: bool = False,
    faithfulness_score: Optional[float] = None
):
    with sqlite3.connect(OBS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO traces 
            (trace_id, timestamp, user_query, generated_sql, retrieved_context, final_response, execution_time_ms, status, hallucination_flag, faithfulness_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace_id,
            datetime.datetime.now().isoformat(),
            user_query,
            generated_sql,
            retrieved_context,
            final_response,
            execution_time_ms,
            status,
            hallucination_flag,
            faithfulness_score
        ))
        conn.commit()

def get_recent_traces(limit: int = 50) -> List[Dict[str, Any]]:
    with sqlite3.connect(OBS_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM traces ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]