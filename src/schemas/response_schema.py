from typing import TypedDict, Literal

class ResponseSchema(TypedDict):
    user_query: str
    query_response: str
    evaluation_state: Literal["True", "False"]
    retry_count: int
    instruction: str
    data_source: Literal["sql", "retriever", ""]
    weather_info: str  # Store weather data separately, append only when answer found
    needs_escalation: bool  # Flag to trigger admin escalation