from src.schemas.response_schema import ResponseSchema
from better_profanity import profanity


# Initialize profanity checker
profanity.load_censor_words()

# Patterns that indicate no answer was found - trigger escalation
ESCALATION_PATTERNS = [
    "i don't know",
    "i do not know",
    "i cannot answer",
    "i'm unable to help",
    "i am unable to help",
    "no information",
    "max retries exceeded",
    "sorry, i am not able to help",
    "please try asking something different",
    "couldn't find information",
    "could not find information",
    "माहिती नाही",
    "माहिती उपलब्ध नाही",
    "क्षमस्व",
    "उपलब्ध नाही",
    "कोणतीही माहिती सापडली नाही"
]

def check_needs_escalation(response: str) -> bool:
    """Check if response indicates inability to answer."""
    response_lower = response.lower()
    return any(pattern in response_lower for pattern in ESCALATION_PATTERNS)


def evaluator_agent(state: ResponseSchema) -> ResponseSchema:
    user_input = state["validated_user_input"]

    query_response = state.get("query_response", "")
    weather_info = state.get("weather_info", "")
    data_source = state.get("data_source", "")
    
    if state.get("retry_count", 0) > 3:
        return {
            "query_response": "I am unable to help with this at the moment, but I would be happy to connect you with an admin for further assistance.",
            "evaluation_state": "True",
            "needs_escalation": True  # Trigger escalation
        }


    # Check if response indicates no answer found
    if check_needs_escalation(query_response):
        return {
            "query_response": "I am unable to help with this at the moment, but I would be happy to connect you with an admin for further assistance.",
            "evaluation_state": "True",
            "needs_escalation": True  # Trigger escalation
        }


    # Check for profanity using better-profanity
    if profanity.contains_profanity(query_response):
        retry_instruction = "Rephrase the response to be completely profanity-free. Avoid any explicit language, slurs, or direct quotes of offensive content. Summarize factually and neutrally."
        return {
            "evaluation_state": "False",
            "instruction": retry_instruction,
            "needs_escalation": False
        }

    else:
        return {
            "evaluation_state": "True",
            "needs_escalation": False
        }

