import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel

load_dotenv()


class LLMFactory:
    """Factory for initializing Groq LLM instances with fallback options."""

    @staticmethod
    def get_llm(temperature: float = 0.1, model_name: str = None) -> BaseChatModel:
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        model = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not groq_api_key or groq_api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not set or valid in backend/.env. "
                "Please configure a valid Groq API Key."
            )

        # Basic Langfuse Observability Integration
        callbacks = []
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                from langfuse.callback import CallbackHandler
                langfuse_handler = CallbackHandler()
                callbacks.append(langfuse_handler)
            except ImportError:
                pass

        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model,
            temperature=temperature,
            callbacks=callbacks if callbacks else None
        )
