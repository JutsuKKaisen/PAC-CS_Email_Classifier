"""
Optimized bilingual (EN/VI) rule set for email-thread classification.
- Precompiled regex patterns (load once).
- Thread-aware: precedence Confirm > Reschedule > Propose, nhìn cửa sổ tail.
- Multi-scheme output giữ nguyên API: classify_labels(subject, messages) -> dict
- O(n) theo số message; không gọi mạng; không phụ thuộc mô hình.

Giữ nguyên tương thích:
  classify_labels(subject: str, messages: List[Dict]) -> Dict[str, Any]
"""
from __future__ import annotations
import re
from typing import List, Dict, Any

# ------------------------------
# Precompiled, bilingual patterns
# ------------------------------
# Scheduling
RE_TIME_PROPOSE = re.compile(
    r"(?:(?:meet(?:ing)?|schedule|call|zoom|teams|hangout|cuộc\s*họp|đặt\s*lịch|họp)\b)"
    r"|(?:\b(?:mon|tue|wed|thu|fri|sat|sun)\b)"
    r"|(?:\bth(?:ứ)?\s*[2-7]\b)"
    r"|(?:\b\d{1,2}[:h\.]\d{2}\b)"
    , re.IGNORECASE
)
RE_TIME_CONFIRM = re.compile(
    r"\b(?:confirm(?:ed)?|see\s*you|approved|ok(?:ay)?|sounds\s*good|"
    r"đã\s*xác\s*nhận|xác\s*nhận|đồng\s*ý|hẹn\s*gặp)\b", re.IGNORECASE
)
RE_TIME_RESCHED = re.compile(
    r"\b(?:re-?schedule|resched|move|postpone|delay|push|"
    r"đổi\s*lịch|hoãn|lùi|chuyển)\b", re.IGNORECASE
)

# Attachments / documents
RE_ATTACH_ATTACHED = re.compile(
    r"\b(?:attached?|attachment|see\s*attachment|pfa|enclosed|đính\s*kèm|tệp\s*đính\s*kèm)\b",
    re.IGNORECASE,
)
RE_ATTACH_EXPECT = re.compile(
    r"(?:(?:send|resend|provide|share|forward)\s*(?:me|us|it)?\s*(?:the\s*)?"
    r"(?:file|doc(?:ument)?s?|attachment|link)\b)"
    r"|(?:vui\s*lòng|xin)\s*(?:gửi|trả\s*lời|chia\s*se)\s*(?:file|tài\s*liệu|đính\s*kèm)\b"
    r"|(?:sẽ\s*gửi|gửi\s*sau|chờ\s*file)",
    re.IGNORECASE,
)

# Urgency
RE_URGENT = re.compile(
    r"\b(?:urgent|asap|eod|by\s*eod|by\s*tomorrow|today|"
    r"khẩn|gấp|ngay|trong\s*ngày|cuối\s*ngày|sớm\s*nhất)\b",
    re.IGNORECASE,
)
RE_LOW = re.compile(
    r"\b(?:no\s*rush|whenever|when\s*free|lúc\s*rảnh|không\s*vội)\b",
    re.IGNORECASE,
)

# Tone
RE_TONE_POS = re.compile(
    r"\b(?:thanks|thank\s*you|appreciate|much\s*appreciated|cheers|"
    r"cảm\s*ơn|trân\s*trọng|tuyệt\s*vời|rất\s*tốt)\b", re.IGNORECASE,
)
RE_TONE_FRUS = re.compile(
    r"\b(?:sorry|apolog(?:y|ise|ize)|frustrat(?:ed|ing)|not\s*happy|angry|"
    r"delay(?:ed)?|blocked|issue|problem|"
    r"xin\s*lỗi|không\s*hài\s*lòng|bực|chậm|trục\s*trặc|vấn\s*đề)\b",
    re.IGNORECASE,
)

# State cues
RE_FOLLOWUP = re.compile(r"\b(?:follow-?up|gentle\s*reminder|ping|nhắc)\b", re.IGNORECASE)
RE_RESOLVED = re.compile(
    r"\b(?:resolved|fixed|done|completed|closed|xong|hoàn\s*tất|đã\s*xử\s*lý)\b",
    re.IGNORECASE,
)

# Request type supplements
RE_REVIEW = re.compile(r"\b(?:review|approve|approval|duyệt|kiểm\s*tra|xác\s*nhận)\b",
                       re.IGNORECASE)
RE_EDIT = re.compile(r"\b(?:edit|revise|revision|chỉnh\s*sửa|sửa)\b", re.IGNORECASE)
RE_PROVIDE_DOCS = re.compile(r"\b(?:doc(?:ument)?s?|file|tài\s*liệu)\b", re.IGNORECASE)
RE_MEET = re.compile(r"\b(?:meet(?:ing)?|schedule|call|họp|lịch|zoom)\b", re.IGNORECASE)


# ------------------------------
# Helpers
# ------------------------------
def _lower(s: str) -> str:
    return s.lower() if isinstance(s, str) else ""

def _last_texts(messages: List[Dict[str, Any]], k: int = 3) -> List[str]:
    """Return lowercased body of last k messages (available)."""
    bodies = [ _lower(m.get("body", "")) for m in messages if m and m.get("body") ]
    return bodies[-k:] if bodies else []


# ------------------------------
# Core classification (thread-aware)
# ------------------------------
def classify_labels(subject: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Drop-in replacement: more robust bilingual rules & precedence.
    """
    subj = _lower(subject)
    bodies = [ _lower(m.get("body", "")) for m in messages if m.get("body") ]
    all_text = " ".join(bodies + [subj])
    last = _last_texts(messages, k=3)  # tail window
    last1 = last[-1] if last else ""
    last_any = " ".join(last)

    # ---- Scheduling outcome (Confirm > Reschedule > Propose > None) ----
    if RE_TIME_CONFIRM.search(last_any):
        scheduling = "CONFIRMED_TIME"
    elif RE_TIME_RESCHED.search(last_any):
        scheduling = "RESCHEDULE"
    elif RE_TIME_PROPOSE.search(all_text):
        scheduling = "PROPOSED_TIME"
    else:
        scheduling = "NO_MEETING"

    # ---- Request type (priority: meet > provide docs > review > edit > info) ----
    if RE_MEET.search(all_text) or scheduling in {"PROPOSED_TIME", "CONFIRMED_TIME", "RESCHEDULE"}:
        request_type = "SCHEDULE/MEET"
    elif RE_ATTACH_EXPECT.search(all_text) and not RE_ATTACH_ATTACHED.search(all_text):
        request_type = "PROVIDE_DOCS"
    elif RE_REVIEW.search(all_text):
        request_type = "REVIEW/APPROVE"
    elif RE_EDIT.search(all_text):
        request_type = "EDIT/REVISE"
    elif RE_PROVIDE_DOCS.search(all_text):
        request_type = "PROVIDE_DOCS"
    else:
        request_type = "INFO_ONLY"

    # ---- Attachments (multi-label) ----
    attachments = []
    if RE_ATTACH_ATTACHED.search(all_text):
        attachments.append("ATTACHED")
    if RE_ATTACH_EXPECT.search(all_text):
        attachments.append("EXPECTING_ATTACHMENT")
    if not attachments:
        attachments = ["NONE_MENTIONED"]

    # ---- Urgency ----
    if RE_URGENT.search(all_text):
        urgency = "URGENT-24H"
    elif RE_LOW.search(all_text):
        urgency = "LOW-120H"
    else:
        urgency = "STD-48H"

    # ---- Tone (prefer last message) ----
    if RE_TONE_FRUS.search(last1) and not RE_TONE_POS.search(last1):
        tone = "FRUSTRATED"
    elif RE_TONE_POS.search(last1) and not RE_TONE_FRUS.search(last1):
        tone = "POSITIVE"
    else:
        # fall back to any tone seen across the tail
        if RE_TONE_POS.search(last_any) and not RE_TONE_FRUS.search(last_any):
            tone = "POSITIVE"
        elif RE_TONE_FRUS.search(last_any) and not RE_TONE_POS.search(last_any):
            tone = "FRUSTRATED"
        else:
            tone = "NEUTRAL"

    # ---- Thread state ----
    n = len(messages)
    if RE_RESOLVED.search(last_any):
        thread_state = "RESOLVED"
    elif RE_FOLLOWUP.search(all_text) or n > 1:
        thread_state = "FOLLOW-UP"
    else:
        thread_state = "NEW"

    return {
        "request_type": request_type,
        "urgency": urgency,
        "thread_state": thread_state,
        "scheduling": scheduling,
        "attachments": attachments,
        "tone": tone,
    }
