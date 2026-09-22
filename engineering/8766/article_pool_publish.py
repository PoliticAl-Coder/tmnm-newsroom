"""Fresh 8766 Article Pool -> validated clean publisher integration. OFFLINE/MOCK Phase 1 only."""
from __future__ import annotations
import hashlib, json, re
from dataclasses import dataclass
from .core import Publisher, PublishError

TMNM_PAGE_ID="1021402681056527"
_GUID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

def canonical_payload(article):
    return {"article_guid":article["article_guid"],"destination_page_id":article["destination_page_id"],"message":article["message"]}

def payload_sha256(article):
    return hashlib.sha256(json.dumps(canonical_payload(article),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class ArticlePoolPublishResult:
    ok: bool
    state: str
    article_guid: str
    attempt_id: str|None=None
    post_id: str|None=None
    error: str|None=None
    receipt: dict|None=None

class ArticlePoolPublishAction:
    """The ONE explicit Phase-1 Publish action exposed to fresh 8766 Article Pool."""
    def __init__(self,publisher:Publisher): self.publisher=publisher
    def publish(self,article):
        guid=str(article.get("article_guid",""))
        try:
            if article.get("approved") is not True: raise ValueError("APPROVED_REQUIRED")
            if not _GUID.fullmatch(guid): raise ValueError("INVALID_ARTICLE_GUID")
            if article.get("destination_page_id")!=TMNM_PAGE_ID: raise ValueError("DESTINATION_MISMATCH")
            if not isinstance(article.get("message"),str) or not article["message"].strip(): raise ValueError("MESSAGE_REQUIRED")
            expected=payload_sha256(article)
            if article.get("payload_sha256")!=expected: raise ValueError("PAYLOAD_HASH_MISMATCH")
            out=self.publisher.publish(guid,True,TMNM_PAGE_ID,article["message"],expected)
            return ArticlePoolPublishResult(ok=out.get("state")=="PUBLISHED",state=out.get("state","HOLD"),article_guid=guid,attempt_id=out.get("attempt_id"),post_id=out.get("post_id"),error=out.get("error"),receipt=out)
        except (ValueError,PublishError) as e:
            return ArticlePoolPublishResult(False,"HOLD",guid,error=str(e))
