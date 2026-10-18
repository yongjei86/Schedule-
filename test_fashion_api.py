import sys, types, tempfile, sqlite3, datetime, html, os
from zoneinfo import ZoneInfo
from flask import Flask, Response
root=os.path.dirname(os.path.abspath(__file__))
main=types.ModuleType('home_tasks_only_app')
main.app=Flask(__name__,template_folder=root+'/templates',static_folder=root+'/static')
main.app.secret_key='isolated-fashion-test'
main.Response=Response
main.datetime=datetime.datetime
main.KST=ZoneInfo('Asia/Seoul')
main.H=html.escape
main._reading_section=lambda *args:'reading'
def qdate(s):
    try:return datetime.datetime.strptime(s,'%Y-%m-%d').date()
    except:return None
main.qdate=qdate
tmp=tempfile.NamedTemporaryFile(suffix='.db',delete=False);tmp.close()
def db():
    c=sqlite3.connect(tmp.name);c.row_factory=sqlite3.Row;return c
main.db=db
sys.modules['home_tasks_only_app']=main
import riley_creative, riley_fashion
client=main.app.test_client()
assert client.get('/riley/coloring').status_code==200
assert client.get('/riley/fashion').status_code==200
with client.session_transaction() as s:token=s['creative_token']
headers={'X-Creative-Token':token}
assert client.post('/riley/fashion/item',json={}).status_code==403
stroke={'color':'#a876bc','size':18,'erase':False,'points':[[180,250],[240,300],[620,400]]}
ids={}
for template in riley_fashion.TEMPLATES:
    r=client.post('/riley/fashion/item',json={'template':template,'title':'지유의 옷','strokes':[stroke],'ready':True},headers=headers)
    assert r.status_code==200,(template,r.status_code)
    ids[template]=r.json['id']
state=riley_fashion.default_state()
state['models']['girl']['outfit']={'top':ids['short-top'],'bottom':ids['long-skirt'],'outer':ids['puffer'],'head':ids['hairpin'],'hand':ids['teddy']}
state['models']['girl']['location']='runway'
assert client.post('/riley/fashion/state',json=state,headers=headers).status_code==200
saved=client.get('/riley/fashion/data').json
assert saved['state']['models']['girl']['location']=='runway'
before=saved['state']['models']['girl']['outfit'].copy()
state['models']['girl']['location']='closet'
assert client.post('/riley/fashion/state',json=state,headers=headers).status_code==200
assert client.get('/riley/fashion/data').json['state']['models']['girl']['outfit']==before
assert client.post('/riley/fashion/item',json={'template':[]},headers=headers).status_code==400
assert client.post('/riley/fashion/item',json={'template':'dress','strokes':[{**stroke,'points':[[900,0]]}]},headers=headers).status_code==400
bad=riley_fashion.default_state();bad['models']['girl']['outfit']={'head':ids['trousers']}
assert client.post('/riley/fashion/state',json=bad,headers=headers).status_code==400
bad=riley_fashion.default_state();bad['models']['girl']['outfit']={'top':'missing'}
assert client.post('/riley/fashion/state',json=bad,headers=headers).status_code==400
assert '옷 디자인' in main._reading_section('지유','/riley')
assert main._reading_section('혜온','/hyeon')=='reading'
assert len(saved['items'])==16
assert next(i for i in saved['items'] if i['id']==ids['short-top'])['strokes'][0]['points'][-1]==[620,400]
print('PASS: 16 garments, freehand spill preservation, layered outfit save/reload, runway return retains outfit, CSRF and invalid payload validation, Riley-only navigation')
os.unlink(tmp.name)
