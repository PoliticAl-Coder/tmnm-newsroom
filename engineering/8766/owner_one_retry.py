"""TMNM 8766 final one-retry owner launcher. One canonical image+message proof only."""
from __future__ import annotations
import hashlib,json,pathlib,uuid,urllib.error,urllib.request
from article_pool_publish import ArticlePoolPublishAction,payload_sha256
from meta_connect import ProtectedTokenStore,GRAPH_VERSION
from tmnm_fb_publisher.core import Store,Publisher,payload_hash
GUID="TMNM-20260911-FB-OWNER-PROOF-01"
PAGE_ID="1021402681056527"
MESSAGE="TMNM FACEBOOK OWNER-PROOF TEST — NO NEWS CONTENT\nTechnical publishing-path verification only.\nPackage: TMNM-20260911-FB-OWNER-PROOF-01\nThis temporary test post may be deleted after verification."
CANONICAL_PAYLOAD_SHA256="F0B5CACFC131908D377D19BD358BDB250C25DBA35DA322F0498A66635DCEA959"
IMAGE_FILENAME="TMNM-20260911-FB-OWNER-PROOF-01_TESTING-1-2-3.png"
IMAGE_SHA256="5FD5A1350B72E16E70A10587CE8282FEFE4A66612FDDDB392EFCFF46EE31CB8E"
MAX_META_WRITE_ATTEMPTS=1
RETRY_AUTHORITY="MASTER-20260924-492"
RETRY_REASON="One bounded retry after proven superseded text-only route defect; preserve first FAILED_DEFINITE history."

def sha256_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest().upper()

def multipart(message,token,image_bytes):
 boundary="----TMNM8766"+uuid.uuid4().hex
 def field(name,value):
  return (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode()
 body=field("message",message)+field("access_token",token)
 body+=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"; filename=\"{IMAGE_FILENAME}\"\r\nContent-Type: image/png\r\n\r\n").encode()+image_bytes+b"\r\n"+f"--{boundary}--\r\n".encode()
 return body,"multipart/form-data; boundary="+boundary

def safe_meta_error(e):
 status=str(getattr(e,"code","UNKNOWN")); typ="UNKNOWN";code="UNKNOWN";sub="NONE";trace="NONE";msg="Meta rejected the request"
 try:
  body=json.loads(e.read().decode("utf-8","replace"));err=body.get("error") or {}
  typ=str(err.get("type","UNKNOWN"));code=str(err.get("code","UNKNOWN"));sub=str(err.get("error_subcode","NONE"));trace=str(err.get("fbtrace_id","NONE"))
  msg=str(err.get("message") or msg).replace("\n"," ").replace("\r"," ")[:300]
 except Exception:pass
 return f"META_HTTP_STATUS={status}|META_ERROR_TYPE={typ}|META_ERROR_CODE={code}|META_ERROR_SUBCODE={sub}|SAFE_META_MESSAGE={msg}|FBTRACE_ID={trace}"

class OneRetryPhotoTransport:
 def __init__(self,token,image_path,opener=urllib.request.urlopen):self.token=token;self.image_path=pathlib.Path(image_path);self.opener=opener;self.write_count=0
 def publish(self,*,page_id,message,attempt_id):
  if self.write_count>=MAX_META_WRITE_ATTEMPTS:raise RuntimeError("MAX_ONE_WRITE")
  if page_id!=PAGE_ID or message!=MESSAGE:return {"kind":"definite_failure","error":"BOUNDARY_MISMATCH"}
  if sha256_file(self.image_path)!=IMAGE_SHA256:return {"kind":"definite_failure","error":"IMAGE_HASH_MISMATCH"}
  body,ctype=multipart(message,self.token,self.image_path.read_bytes());self.write_count+=1
  req=urllib.request.Request(f"https://graph.facebook.com/{GRAPH_VERSION}/{PAGE_ID}/photos",data=body,method="POST",headers={"Content-Type":ctype})
  try:
   with self.opener(req,timeout=60) as r:out=json.loads(r.read().decode("utf-8","replace"))
  except urllib.error.HTTPError as e:return {"kind":"definite_failure","error":safe_meta_error(e)}
  except Exception:return {"kind":"ambiguous"}
  pid=(out.get("post_id") or out.get("id")) if isinstance(out,dict) else None
  return {"kind":"success","post_id":str(pid)} if pid else {"kind":"ambiguous"}

def article():
 if CANONICAL_PAYLOAD_SHA256!="F0B5CACFC131908D377D19BD358BDB250C25DBA35DA322F0498A66635DCEA959":raise RuntimeError("CANONICAL_PAYLOAD_BINDING")
 a={"article_guid":GUID,"approved":True,"destination_page_id":PAGE_ID,"message":MESSAGE};a["payload_sha256"]=payload_sha256(a);return a

def run(base_dir=None,package_dir=None,writer_factory=None):
 root=pathlib.Path(base_dir or pathlib.Path.home()/".tmnm8766");pkg=pathlib.Path(package_dir or pathlib.Path(__file__).parent)
 image=pkg/IMAGE_FILENAME
 if sha256_file(image)!=IMAGE_SHA256:raise RuntimeError("IMAGE_HASH_MISMATCH")
 token_path=root/"meta_token.dpapi"
 if not token_path.is_file():raise RuntimeError("DPAPI_CREDENTIAL_NOT_FOUND")
 token=ProtectedTokenStore(str(token_path)).load();store=Store(root/"publisher.sqlite3")
 prior=store.get(GUID)
 if not prior or prior.get("state")!="FAILED_DEFINITE":raise RuntimeError("RETRY_NOT_ELIGIBLE")
 if prior.get("page_id")!=PAGE_ID or prior.get("payload_sha256")!=payload_hash(MESSAGE):raise RuntimeError("FAILED_RECEIPT_BINDING_MISMATCH")
 store.authorize_retry(GUID,RETRY_AUTHORITY,RETRY_REASON)
 writer=(writer_factory(token,image) if writer_factory else OneRetryPhotoTransport(token,image))
 action=ArticlePoolPublishAction(Publisher(store,writer));first=action.publish(article());receipt=store.get(GUID);second=action.publish(article())
 blocked=(writer.write_count==1 and second.state in ("PUBLISHED","PENDING","AMBIGUOUS","FAILED_DEFINITE","RECONCILING","RECONCILED_PUBLISHED","RECONCILED_NOT_FOUND","HOLD"))
 return first,receipt,second,writer.write_count,blocked

def result_text(first,receipt,writes,blocked):
 durable="PASS" if receipt and receipt.get("state")=="PUBLISHED" and receipt.get("post_id") else ("PRESENT_"+str(receipt.get("state")) if receipt else "NONE")
 err=first.error or (receipt.get("error") if receipt else None) or "NONE"
 return "\n".join(["TMNM 8766 OWNER ONE RETRY","GUID="+GUID,"PAGE_ID="+PAGE_ID,"CANONICAL_PAYLOAD_SHA256="+CANONICAL_PAYLOAD_SHA256,"IMAGE_SHA256="+IMAGE_SHA256,"FACEBOOK_WRITE_COUNT="+str(writes),"POST_ID="+str(first.post_id or "NONE"),"PUBLISH_STATE="+first.state,"DURABLE_RECEIPT="+durable,"SECOND_INVOCATION_BLOCKED="+("PASS" if blocked else "HOLD"),"ERROR="+str(err)])+"\n"

def main():
 out=pathlib.Path(__file__).with_name("TMNM_8766_OWNER_ONE_RETRY_RESULT.txt")
 try:
  first,receipt,second,writes,blocked=run();txt=result_text(first,receipt,writes,blocked);rc=0 if first.state=="PUBLISHED" and first.post_id and blocked and writes==1 else 2
 except Exception as e:
  txt="TMNM 8766 OWNER ONE RETRY\nGUID="+GUID+"\nPAGE_ID="+PAGE_ID+"\nCANONICAL_PAYLOAD_SHA256="+CANONICAL_PAYLOAD_SHA256+"\nIMAGE_SHA256="+IMAGE_SHA256+"\nFACEBOOK_WRITE_COUNT=0\nPOST_ID=NONE\nPUBLISH_STATE=HOLD\nDURABLE_RECEIPT=NONE\nSECOND_INVOCATION_BLOCKED=NOT_TESTED\nERROR="+type(e).__name__+":"+str(e)+"\n";rc=2
 out.write_text(txt,encoding="utf-8");print(txt,end="");return rc
if __name__=="__main__":raise SystemExit(main())
