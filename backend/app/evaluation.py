from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
from langchain_community.chat_models import ChatOpenAI
from app.config import settings

def evaluate_with_ragas(user_query: str, retrieved_context: str, generated_answer: str, ground_truth: str = ""):
    ragas_llm = ChatOpenAI(
        model=settings.SQL_LLM_MODEL,
        openai_api_base=settings.LM_STUDIO_BASE_URL,
        openai_api_key=settings.LM_STUDIO_API_KEY,
        temperature=0.0
    )

    data = {
        "question": [user_query],
        "contexts": [[retrieved_context]],
        "answer": [generated_answer]
    }
    if ground_truth:
        data["ground_truth"] = [ground_truth]

    dataset = Dataset.from_dict(data)
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=ragas_llm
    )
    return result.to_pandas().to_dict(orient="records")[0]