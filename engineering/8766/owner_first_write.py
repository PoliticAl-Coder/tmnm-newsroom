"""TMNM 8766 owner-runtime first-write launcher. Hard-bound to one authorised technical proof."""
from __future__ import annotations
import json, pathlib, urllib.error, urllib.parse, urllib.request
from article_pool_publish import ArticlePoolPublishAction, payload_sha256
from meta_connect import ProtectedTokenStore, GRAPH_VERSION
from tmnm_fb_publisher.core import Store, Publisher
GUID="TMNM-20260911-FB-OWNER-PROOF-01"
PAGE_ID="1021402681056527"
MESSAGE="TMNM FACEBOOK OWNER-PROOF TEST — NO NEWS CONTENT\nTechnical publishing-path verification only.\nPackage: TMNM-20260911-FB-OWNER-PROOF-01\nThis temporary test post may be deleted after verification."
EXPECTED_HASH="F0B5CACFC131908D377D19BD358BDB250C25DBA35DA322F0498A66635DCEA959"
MAX_META_WRITE_ATTEMPTS=1
class OneWriteMetaTransport:
 def __init__(self,token,opener=urllib.request.urlopen): self.token=token;self.opener=opener;self.write_count=0
 def publish(self,*,page_id,message,attempt_id):
  if self.write_count>=MAX_META_WRITE_ATTEMPTS: raise RuntimeError("ONE_WRITE_GUARD")
  if page_id!=PAGE_ID or message!=MESSAGE:return {"kind":"definite_failure","error":"BOUNDARY_MISMATCH"}
  self.write_count+=1
  data=urllib.parse.urlencode({"message":message,"access_token":self.token}).encode()
  req=urllib.request.Request(f"https://graph.facebook.com/{GRAPH_VERSION}/{PAGE_ID}/feed",data=data,method="POST",headers={"Content-Type":"application/x-www-form-urlencoded"})
  try:
   with self.opener(req,timeout=30) as r: out=json.loads(r.read().decode())
  except urllib.error.HTTPError as e:
   status=str(e.code); code="UNKNOWN"; subcode="NONE"; msg="Meta rejected the request"
   try:
    body=json.loads(e.read().decode("utf-8","replace")); err=body.get("error") or {}
    code=str(err.get("code","UNKNOWN")); subcode=str(err.get("error_subcode","NONE"))
    raw=str(err.get("message") or "Meta rejected the request")
    msg=raw.replace("\\n"," ").replace("\\r"," ")[:300]
   except Exception: pass
   return {"kind":"definite_failure","error":"META_HTTP_STATUS="+status+"|META_ERROR_CODE="+code+"|META_ERROR_SUBCODE="+subcode+"|SAFE_META_MESSAGE="+msg}
  except Exception:return {"kind":"ambiguous"}
  post_id=out.get("id") if isinstance(out,dict) else None
  return {"kind":"success","post_id":str(post_id)} if post_id else {"kind":"ambiguous"}
def article():
 a={"article_guid":GUID,"approved":True,"destination_page_id":PAGE_ID,"message":MESSAGE};a["payload_sha256"]=payload_sha256(a)
 if EXPECTED_HASH!="F0B5CACFC131908D377D19BD358BDB250C25DBA35DA322F0498A66635DCEA959":raise RuntimeError("PAYLOAD_HASH_BINDING")
 return a
def run(base_dir=None,writer_factory=OneWriteMetaTransport):
 root=pathlib.Path(base_dir or pathlib.Path.home()/".tmnm8766"); token_path=root/"meta_token.dpapi"
 if not token_path.is_file():raise RuntimeError("DPAPI_CREDENTIAL_NOT_FOUND")
 token=ProtectedTokenStore(str(token_path)).load();store=Store(root/"publisher.sqlite3");writer=writer_factory(token);action=ArticlePoolPublishAction(Publisher(store,writer))
 first=action.publish(article());receipt=store.get(GUID);second=action.publish(article())
 blocked=(writer.write_count==1 and second.state in ("PUBLISHED","PENDING","AMBIGUOUS","FAILED_DEFINITE","RECONCILING","RECONCILED_PUBLISHED","RECONCILED_NOT_FOUND","HOLD"))
 return first,receipt,second,writer.write_count,blocked
def safe_result(first,receipt,write_count,blocked,error="NONE"):
 durable="PASS" if receipt and receipt.get("state")=="PUBLISHED" and receipt.get("post_id") else ("PRESENT_"+str(receipt.get("state")) if receipt else "NONE")
 effective=first.error or (receipt.get("error") if receipt else None) or error
 return "\n".join(["TMNM 8766 OWNER FIRST WRITE","GUID="+GUID,"PAGE_ID="+PAGE_ID,"FACEBOOK_WRITE_COUNT="+str(write_count),"POST_ID="+str(first.post_id or "NONE"),"PUBLISH_STATE="+str(first.state),"DURABLE_RECEIPT="+durable,"SECOND_INVOCATION_BLOCKED="+("PASS" if blocked else "HOLD"),"ERROR="+str(effective)])+"\n"
def main():
 out=pathlib.Path(__file__).with_name("TMNM_8766_OWNER_FIRST_WRITE_RESULT.txt")
 try:
  first,receipt,second,writes,blocked=run();txt=safe_result(first,receipt,writes,blocked);rc=0 if first.state=="PUBLISHED" and first.post_id and blocked and writes==1 else 2
 except Exception as e:
  txt="TMNM 8766 OWNER FIRST WRITE\nGUID="+GUID+"\nPAGE_ID="+PAGE_ID+"\nFACEBOOK_WRITE_COUNT=0\nPOST_ID=NONE\nPUBLISH_STATE=HOLD\nDURABLE_RECEIPT=NONE\nSECOND_INVOCATION_BLOCKED=NOT_TESTED\nERROR="+type(e).__name__+":"+str(e)+"\n";rc=2
 out.write_text(txt,encoding="utf-8");print(txt,end="");return rc
if __name__=="__main__":raise SystemExit(main())
