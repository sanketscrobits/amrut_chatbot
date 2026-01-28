from src.schemas.response_schema import ResponseSchema
from better_profanity import profanity


# Initialize profanity checker
profanity.load_censor_words()

def evaluator_agent(state: ResponseSchema) -> ResponseSchema:
    user_query = state["user_query"]
    query_response = state["query_response"]
    llm_text = query_response
    if state["retry_count"] > 3:
        return {
            "user_query": user_query,
            "query_response": "Max retries exceeded. Response could not be generated without profanity.",
            "evaluation_state": "True",
            "instruction": "" 
        }

    # Check for profanity using better-profanity
    if profanity.contains_profanity(llm_text):
        retry_instruction = "Rephrase the response to be completely profanity-free. Avoid any explicit language, slurs, or direct quotes of offensive content. Summarize factually and neutrally."
        return {
            "user_query": user_query,
            "query_response": llm_text,  
            "evaluation_state": "False",
            "instruction": retry_instruction
        }
    else:
        return {
            "user_query": user_query,
            "query_response": llm_text, 
            "evaluation_state": "True",
            "instruction": ""
        }