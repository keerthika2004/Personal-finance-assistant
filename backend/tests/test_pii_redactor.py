import pytest
from backend.app.services.pii_redactor import PIIRedactor

def test_redact_credit_card():
    text = "My card is 1234-5678-9012-3456 and it works."
    redacted = PIIRedactor.redact(text)
    assert redacted == "My card is [REDACTED_CC] and it works."
    
    text2 = "Card 1234567890123456"
    redacted2 = PIIRedactor.redact(text2)
    assert redacted2 == "Card [REDACTED_CC]"

def test_redact_ssn():
    text = "My SSN is 123-45-6789."
    redacted = PIIRedactor.redact(text)
    assert redacted == "My SSN is [REDACTED_SSN]."

def test_redact_phone():
    text = "Call me at 555-123-4567."
    redacted = PIIRedactor.redact(text)
    assert redacted == "Call me at [REDACTED_PHONE]."
    
    text2 = "Phone (555) 123-4567"
    redacted2 = PIIRedactor.redact(text2)
    assert redacted2 == "Phone [REDACTED_PHONE]"

def test_no_pii():
    text = "This is a normal coffee transaction for 5.50."
    redacted = PIIRedactor.redact(text)
    assert redacted == text

def test_empty_string():
    assert PIIRedactor.redact("") == ""
    assert PIIRedactor.redact(None) is None
