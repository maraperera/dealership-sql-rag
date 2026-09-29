from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import engine
from app.observability import init_observability_db, get_recent_traces
from app.rag_engine import run_rag_pipeline
from app.evaluation import evaluate_with_ragas

app = FastAPI(title="Dealership SQL-RAG Core API", version="1.0.0")

class QueryRequest(BaseModel):
    query: str

class EvalRequest(BaseModel):
    user_query: str
    retrieved_context: str
    generated_answer: str
    ground_truth: Optional[str] = ""

@app.on_event("startup")
def startup_event():
    init_observability_db()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/rag/query")
def execute_query(req: QueryRequest):
    result = run_rag_pipeline(req.query)
    if "error" in result and "results" not in result:
        raise HTTPException(status_code=500, detail=result)
    return result

@app.get("/api/observability/traces")
def fetch_traces(limit: int = 50):
    return get_recent_traces(limit)

@app.post("/api/eval/ragas")
def run_evaluation(req: EvalRequest):
    try:
        metrics = evaluate_with_ragas(
            req.user_query,
            req.retrieved_context,
            req.generated_answer,
            req.ground_truth
        )
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/eval/batch")
def run_batch_evaluation(limit: int = 10):
    traces = get_recent_traces(limit)
    valid_traces = [t for t in traces if t.get("status") == "SUCCESS"]
    
    results = []
    for trace in valid_traces:
        try:
            score = evaluate_with_ragas(
                user_query=trace["user_query"],
                retrieved_context=trace["retrieved_context"],
                generated_answer=trace["final_response"]
            )
            results.append({
                "trace_id": trace["trace_id"],
                "query": trace["user_query"],
                "faithfulness": float(score.get("faithfulness", 0.0) or 0.0),
                "answer_relevancy": float(score.get("answer_relevancy", 0.0) or 0.0)
            })
        except Exception as e:
            # Fallback for individual item failures
            results.append({
                "trace_id": trace["trace_id"],
                "query": trace["user_query"],
                "faithfulness": 0.0,
                "answer_relevancy": 0.0
            })
            
    return {"total_evaluated": len(results), "evaluations": results}