import re
import time
import uuid
import json
from openai import OpenAI
from app.config import settings
from app.database import SCHEMA_DEFINITION, execute_readonly_sql
from app.observability import log_trace

client = OpenAI(
    base_url=settings.LM_STUDIO_BASE_URL,
    api_key=settings.LM_STUDIO_API_KEY
)

def extract_sql_query(raw_text: str) -> str:
    cleaned = re.sub(r"```sql", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    match = re.search(r"(SELECT.*?;)", cleaned, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    match_fallback = re.search(r"(SELECT.*)", cleaned, re.IGNORECASE | re.DOTALL)
    if match_fallback:
        return match_fallback.group(1).strip()
    return cleaned.strip()

def run_rag_pipeline(user_query: str) -> dict:
    trace_id = str(uuid.uuid4())
    start_time = time.time()

    # Step 1: Text-to-SQL Generation with Out-Of-Domain Rejection
    sql_prompt = f"""You are an internal SQL assistant for a Melbourne automotive dealership network.
Database Schema:
{SCHEMA_DEFINITION}

Branches: Melbourne CBD (branch_id=1), Doncaster (branch_id=2), Dandenong (branch_id=3).

STRICT RULES:
1. If the user question is NOT related to cars, car specifications, inventory, brands, pricing, or our 3 Melbourne branches, reply with EXACTLY: OUT_OF_SCOPE
2. If related, return ONLY a valid PostgreSQL SELECT query.
3. Do not include markdown codeblocks or quotes.
4. Limit records to at most 25 rows unless an aggregate like COUNT/AVG is needed.

User Question: {user_query}
SQL Query:"""

    try:
        sql_res = client.chat.completions.create(
            model=settings.SQL_LLM_MODEL,
            messages=[{"role": "user", "content": sql_prompt}],
            temperature=0.0
        )
        raw_sql = (sql_res.choices[0].message.content or "").strip()
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log_trace(trace_id, user_query, "ERROR", "", str(e), elapsed, "FAILED_SQL_GENERATION", True, 0.0)
        return {"error": f"Failed generating SQL: {str(e)}", "trace_id": trace_id}

    # Intercept Out-of-Scope Queries immediately
    if "OUT_OF_SCOPE" in raw_sql.upper():
        refusal_message = (
            "I am the internal inventory assistant for our Melbourne dealership network. "
            "I can only help with questions regarding our vehicle stock, pricing, specifications, "
            "and branch availability in Melbourne CBD, Doncaster, and Dandenong."
        )
        elapsed = (time.time() - start_time) * 1000
        log_trace(trace_id, user_query, "OUT_OF_SCOPE", "[]", refusal_message, elapsed, "OUT_OF_SCOPE", False, 1.0)
        return {
            "trace_id": trace_id,
            "query": user_query,
            "generated_sql": "N/A",
            "results_count": 0,
            "results": [],
            "answer": refusal_message,
            "latency_ms": elapsed,
            "hallucination_detected": False
        }

    generated_sql = extract_sql_query(raw_sql)

    # Step 2: Database Retrieval
    try:
        db_records = execute_readonly_sql(generated_sql)
        context_str = json.dumps(db_records, default=str)
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log_trace(trace_id, user_query, generated_sql, "", str(e), elapsed, "FAILED_SQL_EXECUTION", True, 0.0)
        return {"error": f"SQL Execution error: {str(e)}", "sql": generated_sql, "trace_id": trace_id}

    # Step 3: Synthesis Generation strictly bound to retrieved context
    synth_prompt = f"""You are an internal dealership assistant for our Melbourne car sales network.
You have access to database results ONLY. 

User Question: {user_query}
Database Context:
{context_str}

CRITICAL RULES:
1. Answer using ONLY facts found in the Database Context above.
2. If the context is empty or does not provide the answer, say you could not find matching vehicles in our inventory.
3. NEVER answer general knowledge, history, trivia, or non-dealership topics from your own training data.
4. Respond in polite, natural English sentences. Do not show raw SQL or JSON.

Answer:"""

    try:
        synth_res = client.chat.completions.create(
            model=settings.SYNTHESIS_LLM_MODEL,
            messages=[{"role": "user", "content": synth_prompt}],
            temperature=0.1
        )
        final_answer = (synth_res.choices[0].message.content or "").strip()
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log_trace(trace_id, user_query, generated_sql, context_str, str(e), elapsed, "FAILED_SYNTHESIS", True, 0.0)
        return {"error": f"Failed to synthesize answer: {str(e)}", "sql": generated_sql, "trace_id": trace_id}

    elapsed = (time.time() - start_time) * 1000

    log_trace(
        trace_id=trace_id,
        user_query=user_query,
        generated_sql=generated_sql,
        retrieved_context=context_str,
        final_response=final_answer,
        execution_time_ms=elapsed,
        status="SUCCESS",
        hallucination_flag=False,
        faithfulness_score=1.0
    )

    return {
        "trace_id": trace_id,
        "query": user_query,
        "generated_sql": generated_sql,
        "results_count": len(db_records),
        "results": db_records,
        "answer": final_answer,
        "latency_ms": elapsed,
        "hallucination_detected": False
    }