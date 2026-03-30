from typing import Optional

from fastapi import APIRouter, Form, UploadFile

from app.schemas.ai import OCRResponse
from app.services.ocr_service import OCRService

router = APIRouter()

_ocr_service = OCRService()


@router.post("/notices/ocr", response_model=OCRResponse)
async def ocr_notice(
    source_name: str = Form(...),
    uploaded_at: str = Form(...),
    raw_text: Optional[str] = Form(None),
    upload: Optional[UploadFile] = None,
) -> OCRResponse:
    """공지 텍스트 요약 및 이행 체크리스트 추출 API"""
    return await _ocr_service.parse_notice(
        upload=upload,
        raw_text=raw_text,
        source_name=source_name,
        uploaded_at=uploaded_at,
    )