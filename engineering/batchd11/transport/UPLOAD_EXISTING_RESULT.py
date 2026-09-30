import sys,os
from pathlib import Path
sys.path.insert(0,str(Path(os.environ["LOCALAPPDATA"])/"TMNM"/"LocalWorker"/"app"))
from google_auth import build_drive_service
from googleapiclient.http import MediaFileUpload
f=Path(sys.argv[1]); svc=build_drive_service()
r=svc.files().create(body={"name":f.name},media_body=MediaFileUpload(str(f),mimetype="application/zip",resumable=False),fields="id,size").execute()
print(r["id"])
