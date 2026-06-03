from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ConversationMessage(BaseModel):
    role: str
    content: str


class AnalyseRequest(BaseModel):
    conversation: List[ConversationMessage]
    user_id: str
    publisher_key: str
    session_id: Optional[str] = None
    trip_confirmed: Optional[bool] = False
    days_before_departure: Optional[int] = None
    conversation_ended: Optional[bool] = False
    requested_format: Optional[str] = None


class AdPayloadResponse(BaseModel):
    ad: Optional[Dict[str, Any]] = None
    format: Optional[str] = None
    triggered_by: Optional[str] = None
    session_id: Optional[str] = None


class ImpressionRequest(BaseModel):
    ad_id: str
    user_id: str
    publisher_key: str
    format: str
    timestamp: Optional[str] = None


class ClickRequest(BaseModel):
    ad_id: str
    user_id: str
    publisher_key: str
    format: str
    cta_url: str
    timestamp: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    code: str
    detail: Optional[str] = None
