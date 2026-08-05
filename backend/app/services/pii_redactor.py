import re

class PIIRedactor:
    """Utility to redact PII (Personal Identifiable Information) before LLM ingestion."""

    # Regex patterns
    CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    PHONE_PATTERN = re.compile(r'(?:\+?1[-.\s]?)?\(?\b\d{3}\b\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')

    @classmethod
    def redact(cls, text: str) -> str:
        if not text:
            return text
            
        # Redact Credit Cards
        redacted = cls.CREDIT_CARD_PATTERN.sub('[REDACTED_CC]', text)
        
        # Redact SSNs
        redacted = cls.SSN_PATTERN.sub('[REDACTED_SSN]', redacted)
        
        # Redact Phone Numbers
        redacted = cls.PHONE_PATTERN.sub('[REDACTED_PHONE]', redacted)
        
        return redacted
