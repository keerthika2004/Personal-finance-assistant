import os
from dotenv import load_dotenv
try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None
try:
    from langchain_core.language_models import BaseChatModel
except ImportError:
    BaseChatModel = None

load_dotenv()


class LLMFactory:
    """Factory for Groq LLM instances.
    Two tiers so we don't burn 70B rate limits on easy work:
    - fast = True -> small model (routing, classification, tool-calling)
    - fast = False -> larger model (reasoning / insight generation)
    """

    @staticmethod
    def get_llm(temperature: float = 0.1, model_name: str = None, fast: bool = False) -> BaseChatModel:
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        
        if not groq_api_key or groq_api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not set or valid in backend/.env. "
                "Please configure a valid Groq API Key."
            )

        if model_name:
            model = model_name
        elif fast:
            model = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
        else:
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


        # Basic Langfuse Observability Integration
        callbacks = []
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                from langfuse.langchain import CallbackHandler
                callbacks.append(CallbackHandler())
            except ImportError:
                pass

        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model,
            temperature=temperature,
            max_retries=6, 
            callbacks=callbacks if callbacks else None
        )
