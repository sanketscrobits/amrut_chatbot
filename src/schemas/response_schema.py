from typing import TypedDict, Literal

class ResponseSchema(TypedDict):
    validated_user_input: str
    query_response: str

    evaluation_state: Literal["True", "False", ""]
    retry_count: int
    instruction: str
    data_source: Literal["sql", "retriever", "general", ""]
    weather_info: str
    needs_escalation: bool