
import re

class PIIRedactor:
    """Utility to redact PII (Personal Identifiable Information) before LLM ingestion."""
    # Regex patterns. Order matters: specific patterns run first so a 16-digit card isn't half-eaten by the Aadhar or generic long-number rules.
    EMAIL_PATTERN = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')
    UPI_PATTERN = re.compile(r'\b[\w.-]{2,}@[a-zA-Z]{2,}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
    AADHAAR_PATTERN = re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b') 
    PAN_PATTERN = re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    INDIAN_PHONE_PATTERN = re.compile(r'(?:\+91[-\s]?)?\b[6-9]\d{4}[-\s]?\d{5}\b')
    PHONE_PATTERN = re.compile(r'(?:\+?1[-.\s]?)?\(?\b\d{3}\b\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    #Account numbers, contiguous aadhar, UPI references: any 9-18 digit run
    LONG_NUMBER_PATTERN = re.compile(r'\b\d{9,18}\b')
    
    @classmethod
    def redact(cls, text: str) -> str:
        if not text:
            return text
        redacted = cls.EMAIL_PATTERN.sub('[REDACTED_EMAIL]', text)
        redacted = cls.UPI_PATTERN.sub('[REDACTED_UPI]', redacted)
        redacted = cls.CREDIT_CARD_PATTERN.sub('[REDACTED_CC]', redacted)
        redacted = cls.AADHAAR_PATTERN.sub('[REDACTED_AADHAAR]', redacted)
        redacted = cls.PAN_PATTERN.sub('[REDACTED_PAN]', redacted)
        redacted = cls.SSN_PATTERN.sub('[REDACTED_SSN]', redacted)
        redacted = cls.INDIAN_PHONE_PATTERN.sub('[REDACTED_PHONE]', redacted)
        redacted = cls.PHONE_PATTERN.sub('[REDACTED_PHONE]', redacted)
        redacted = cls.LONG_NUMBER_PATTERN.sub('[REDACTED_NUMBER]', redacted)
        return redacted

        