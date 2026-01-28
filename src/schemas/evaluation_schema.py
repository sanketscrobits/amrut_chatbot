from pydantic import BaseModel
class EvaluationOutput(BaseModel):
    has_hallucinations: bool = False
    citations_complete: bool = True
    evaluation_score: float = 5.0
    evaluation_feedback: str = ""