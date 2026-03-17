from datetime import datetime
from typing import Optional

from fastapi import UploadFile

from app.schemas.ai import OCRChecklistItem, OCRResponse
from app.services.evidence_service import EvidenceService
from app.services.governance_service import GovernanceService
from app.services.safety_service import SafetyService


class OCRService:
    def __init__(self) -> None:
        self.evidence_service = EvidenceService()
        self.governance_service = GovernanceService()
        self.safety_service = SafetyService()

    async def parse_notice(
        self,
        upload: Optional[UploadFile],
        raw_text: Optional[str],
        source_name: str,
        uploaded_at: str,
    ) -> OCRResponse:
        if upload is not None:
            content = await upload.read()
            text = content.decode("utf-8")
            source_name = upload.filename or source_name
        else:
            text = raw_text or ""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        summary = " ".join(lines[:2])[:180] if lines else "공지 내용이 비어 있습니다."
        summary = self.safety_service.mask_text(summary)
        self.safety_service.assert_policy_safe(summary)

        required_actions: list[OCRChecklistItem] = []
        for line in lines:
            if any(token in line for token in ["필수", "반영", "적용", "제출", "점검"]):
                required_actions.append(
                    OCRChecklistItem(item=line, deadline="확인 필요", assignee="store_owner")
                )
        if not required_actions and lines:
            required_actions.append(
                OCRChecklistItem(item=lines[0], deadline="확인 필요", assignee="store_owner")
            )

        parsed_uploaded_at = datetime.fromisoformat(uploaded_at)
        evidence = [
            self.evidence_service.build(
                metric="OCR 원문 길이",
                value=f"{len(text)}자",
                period="업로드 시점",
                source_name=source_name,
                uploaded_at=parsed_uploaded_at,
            )
        ]
        confidence = 0.95 if upload is None else 0.9
        return OCRResponse(
            summary=summary,
            required_actions=required_actions,
            ocr_confidence=confidence,
            raw_text=text,
            evidence=evidence,
            version=self.governance_service.get_version("ocr"),
        )
