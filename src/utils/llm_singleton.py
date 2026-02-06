from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI

class LLMSingleton:
    """Singleton for ChatGoogleGenerativeAI instance."""
    
    _instance: Optional["LLMSingleton"] = None
    _llm: Optional[ChatGoogleGenerativeAI] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_llm(self, model: str = "gemini-2.5-flash", temperature: float = 0) -> ChatGoogleGenerativeAI:
        """
        Get or create the LLM instance.
        Note: If you need a different model/temperature, you might want to extend this
        to support multiple instances by key.
        """
        if self._llm is None:
            # Lazy import to avoid circular dependencies
            from settings import GOOGLE_API_KEY
            
            self._llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=GOOGLE_API_KEY,
            )
        return self._llm

# Module-level variable to store the non-streaming LLM instance
_llm_instance: Optional[ChatGoogleGenerativeAI] = None

def get_llm(model: str = "gemini-2.5-flash", temperature: float = 0) -> ChatGoogleGenerativeAI:
    """
    Get singleton LLM instance.
    This function provides a non-streaming LLM instance.
    """
    global _llm_instance
    from settings import GOOGLE_API_KEY # Ensure GOOGLE_API_KEY is available here

    if _llm_instance is None:
        _llm_instance = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=GOOGLE_API_KEY,
            temperature=temperature,
            streaming=False
        )
    return _llm_instance

def get_streaming_llm(model: str = "gemini-2.5-flash", temperature: float = 0) -> ChatGoogleGenerativeAI:
    """
    Get a new streaming LLM instance.
    Streaming instances are not cached as singletons.
    """
    from settings import GOOGLE_API_KEY # Ensure GOOGLE_API_KEY is available here

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature,
        streaming=True
    )
