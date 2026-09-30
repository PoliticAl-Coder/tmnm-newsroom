import sys,os,traceback
from pathlib import Path
try:
 f=Path(sys.argv[1]); app=Path(os.environ["LOCALAPPDATA"])/"TMNM"/"LocalWorker"/"app"; sys.path.insert(0,str(app))
 from google_auth import build_drive_service
 from googleapiclient.http import MediaFileUpload
 svc=build_drive_service(); r=svc.files().create(body={"name":f.name},media_body=MediaFileUpload(str(f),mimetype="application/zip",resumable=False),fields="id,size").execute()
 meta=svc.files().get(fileId=r["id"],fields="id,size,name").execute()
 if str(meta.get("size"))!=str(f.stat().st_size): raise RuntimeError("DRIVE_SIZE_VERIFY_FAILED")
 print("DRIVE_ID="+r["id"])
except Exception:
 traceback.print_exc(); sys.exit(1)
