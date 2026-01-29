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

def get_llm(model: str = "gemini-2.5-flash", temperature: float = 0) -> ChatGoogleGenerativeAI:
    """Helper function to get the LLM instance."""
    return LLMSingleton().get_llm(model=model, temperature=temperature)
