from typing import TypedDict, Literal

class ResponseSchema(TypedDict):
    user_query: str
    query_response: str
    evaluation_state: Literal["True", "False"]
    retry_count: int
    instruction: str