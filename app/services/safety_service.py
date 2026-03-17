import re

from app.core.config import settings


class SafetyService:
    _phone_pattern = re.compile(r"(\d{2,3})-(\d{3,4})-(\d{4})")
    _email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    _resident_pattern = re.compile(r"\b\d{6}-\d{7}\b")

    def mask_text(self, text: str) -> str:
        if not settings.pii_masking_enabled:
            return text

        text = self._phone_pattern.sub(r"\1-****-\3", text)
        text = self._email_pattern.sub("***@***", text)
        text = self._resident_pattern.sub("******-*******", text)
        return text

    def assert_policy_safe(self, text: str) -> None:
        lowered = text.lower()
        blocked_terms = ["discriminate", "bypass consent", "steal", "fraud"]
        if any(term in lowered for term in blocked_terms):
            raise ValueError("Policy violation detected in generated content")
