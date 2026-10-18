"""Riley's hand-painted wardrobe and persistent runway."""
import json
import math
import re
import secrets
from flask import request, session, jsonify, abort, render_template
from riley_creative import app, connection, token, now

TEMPLATES = {'short-top','long-top','shorts','trousers','mini-skirt','long-skirt','dress','jacket','puffer','hairpin','headband','hairband','phone','bag','book','teddy'}
SLOTS = {'top','bottom','dress','outer','head','hand'}
with connection() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS riley_fashion_items(id TEXT PRIMARY KEY, template TEXT NOT NULL, title TEXT NOT NULL, strokes TEXT NOT NULL, ready INTEGER NOT NULL DEFAULT 0, updated TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS riley_fashion_state(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, updated TEXT NOT NULL);''')

def default_state():
    return {'active':'girl','models':{k:{'name':n,'outfit':{},'location':'closet'} for k,n in [('girl','지유의 여자 모델'),('boy','지유의 남자 모델')]},'gallery':[]}

def verify_fashion():
    if not secrets.compare_digest(request.headers.get('X-Creative-Token',''),session.get('creative_token','!')):
        abort(403)
    if request.content_length and request.content_length>2500000: abort(413)
    data=request.get_json(silent=True)
    if not isinstance(data,dict): abort(400)
    return data

@app.get('/riley/fashion')
def riley_fashion_page():
    response=app.make_response(render_template('riley-fashion.html',token=token()))
    response.headers['Cache-Control']='no-store'
    return response

@app.get('/riley/fashion/data')
def riley_fashion_data():
    with connection() as c:
        items=[dict(r) for r in c.execute('SELECT * FROM riley_fashion_items ORDER BY updated DESC')]
        row=c.execute('SELECT payload FROM riley_fashion_state WHERE id=1').fetchone()
    for item in items: item['strokes']=json.loads(item['strokes'])
    response=jsonify(items=items,state=json.loads(row['payload']) if row else default_state())
    response.headers['Cache-Control']='no-store'
    return response

@app.post('/riley/fashion/item')
def riley_fashion_item():
    data=verify_fashion()
    ident=data.get('id') or secrets.token_hex(12)
    template=data.get('template')
    if not isinstance(ident,str) or not re.fullmatch(r'[a-f0-9]{24}',ident) or not isinstance(template,str) or template not in TEMPLATES: abort(400)
    strokes=data.get('strokes',[])
    if not isinstance(strokes,list) or len(strokes)>800: abort(400)
    total=0
    for stroke in strokes:
        if not isinstance(stroke,dict) or set(stroke)-{'color','size','erase','points'}: abort(400)
        if not isinstance(stroke.get('color'),str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',stroke['color']): abort(400)
        size=stroke.get('size')
        if type(size) not in (int,float) or not math.isfinite(size) or not 1<=size<=100 or type(stroke.get('erase')) is not bool: abort(400)
        points=stroke.get('points')
        if not isinstance(points,list) or not 1<=len(points)<=4000: abort(400)
        total+=len(points)
        if total>100000: abort(400)
        for p in points:
            if not isinstance(p,list) or len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p): abort(400)
            if not -20<=p[0]<=620 or not -20<=p[1]<=820: abort(400)
    with connection() as c:
        c.execute('INSERT INTO riley_fashion_items VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET template=excluded.template,title=excluded.title,strokes=excluded.strokes,ready=excluded.ready,updated=excluded.updated',
                  (ident,template,str(data.get('title') or '내가 만든 옷')[:100],json.dumps(strokes,separators=(',',':')),int(bool(data.get('ready'))),now()))
    return jsonify(id=ident)

def valid_model(model,items):
    if not isinstance(model,dict) or set(model)-{'name','outfit','location'}: return False
    if not isinstance(model.get('name'),str) or len(model['name'])>60 or model.get('location') not in ('closet','runway'): return False
    outfit=model.get('outfit')
    if not isinstance(outfit,dict) or not set(outfit)<=SLOTS: return False
    slot_for={'short-top':'top','long-top':'top','shorts':'bottom','trousers':'bottom','mini-skirt':'bottom','long-skirt':'bottom','dress':'dress','jacket':'outer','puffer':'outer','hairpin':'head','headband':'head','hairband':'head','phone':'hand','bag':'hand','book':'hand','teddy':'hand'}
    return all(isinstance(ident,str) and ident in items and slot_for[items[ident]]==slot for slot,ident in outfit.items())

@app.post('/riley/fashion/state')
def riley_fashion_save_state():
    data=verify_fashion()
    if set(data)!={'active','models','gallery'} or data.get('active') not in ('girl','boy'): abort(400)
    models=data.get('models');gallery=data.get('gallery')
    if not isinstance(models,dict) or set(models)!={'girl','boy'} or not isinstance(gallery,list) or len(gallery)>100: abort(400)
    with connection() as c:
        items={r['id']:r['template'] for r in c.execute('SELECT id,template FROM riley_fashion_items')}
        if not all(valid_model(m,items) for m in models.values()): abort(400)
        for look in gallery:
            if not isinstance(look,dict) or set(look)!={'id','name','kind','model','at'} or not isinstance(look['id'],str) or not re.fullmatch(r'[a-zA-Z0-9-]{1,64}',look['id']): abort(400)
            if look['kind'] not in ('girl','boy') or not isinstance(look['name'],str) or len(look['name'])>100 or not isinstance(look['at'],str) or len(look['at'])>40 or not valid_model(look['model'],items): abort(400)
        c.execute('INSERT INTO riley_fashion_state VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated',(json.dumps(data,ensure_ascii=False),now()))
    return jsonify(ok=True)
