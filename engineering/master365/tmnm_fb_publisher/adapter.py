from .core import Publisher
def control_room_publish(publisher:Publisher,payload:dict)->dict:
 r=publisher.publish(payload).as_dict()
 r['ok']=r['state'] in ('PUBLISHED','RECONCILED_PUBLISHED')
 return r
