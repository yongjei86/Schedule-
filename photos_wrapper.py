import os, json
from pathlib import Path
import requests
from flask import request, jsonify, send_from_directory
import gcal_wrapper as gcal
import app as base

app = gcal.app
PHOTO_DIR = Path('/data/photos/bali-2026')
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = PHOTO_DIR / 'manifest.json'
CLIENT_ID = os.getenv('GOOGLE_PHOTOS_CLIENT_ID', '')
SCOPE = 'https://www.googleapis.com/auth/photospicker.mediaitems.readonly'

_orig_travels = base.travels

def travels_with_photos(done):
    out = _orig_travels(done)
    if done:
        needle = '<td>2026-08-08 ~ 2026-08-17</td><td>인도네시아</td><td>발리</td><td><b>발리</b></td>'
        repl = '<td>2026-08-08 ~ 2026-08-17</td><td>인도네시아</td><td>발리</td><td><b>발리</b><br><a class="btn s" style="display:inline-block;margin-top:6px" href="/photos/bali-2026" onclick="event.stopPropagation()">📷 사진</a></td>'
        out = out.replace(needle, repl, 1)
    return out
base.travels = travels_with_photos

def _manifest():
    if not MANIFEST.exists():
        return []
    try:
        return json.loads(MANIFEST.read_text('utf-8'))
    except Exception:
        return []

def _gallery_html():
    items = _manifest()
    if not items:
        return '<div style="padding:24px;text-align:center;color:#718097">아직 선택한 사진이 없습니다.</div>'
    cards=[]
    for x in items:
        cards.append(f'<div style="width:180px;flex:0 0 180px"><img src="/photos/bali-2026/file/{base.H(x["file"])}" style="width:180px;height:135px;object-fit:cover;border-radius:12px"><div style="font-size:11px;color:#718097;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{base.H(x.get("name",""))}</div></div>')
    return '<div style="display:flex;gap:10px;overflow-x:auto;padding:4px 0 10px">'+''.join(cards)+'</div>'

@app.route('/photos/bali-2026')
def bali_photos():
    ready = bool(CLIENT_ID)
    status = '<span class="pill">Google Photos 연결 준비됨</span>' if ready else '<span class="pill">OAuth 설정 필요</span>'
    body = f'''<div class="toolbar"><div><a class="btn s" href="/past">← 과거 여행</a></div><div>{status}</div></div>
<div class="card" style="max-width:none;margin:0 0 14px"><h2 style="margin-top:0">2026년 8월 발리 사진</h2><p style="color:#718097">Google Photos에서 이 여행 사진만 직접 선택하면 이 페이지에 저장해 두고 계속 볼 수 있게 만든 시험 기능입니다.</p>
<button id="pickBtn" class="btn" {'disabled style="opacity:.5"' if not ready else ''}>Google Photos에서 사진 선택</button><span id="msg" style="margin-left:10px;color:#718097;font-size:13px"></span></div>
<div class="card" style="max-width:none;margin:0"><h3 style="margin-top:0">선택된 사진</h3>{_gallery_html()}</div>
<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
const CLIENT_ID={json.dumps(CLIENT_ID)}; let accessToken='',pickerSession='';
function say(x){{document.getElementById('msg').textContent=x}}
async function beginPicker(token){{
  accessToken=token; say('선택창 준비 중...');
  const r=await fetch('/photos/picker/create',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{access_token:token}})}});
  const j=await r.json(); if(!r.ok){{say(j.error||'연결 실패');return}}
  pickerSession=j.id; window.open(j.pickerUri+'/autoclose','gphotos','width=1000,height=760'); say('Google Photos에서 사진을 고른 뒤 완료를 눌러줘'); poll();
}}
async function poll(){{
  if(!pickerSession)return; const r=await fetch('/photos/picker/status',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{access_token:accessToken,session_id:pickerSession}})}}); const j=await r.json();
  if(j.ready){{say('사진 저장 중...'); const s=await fetch('/photos/picker/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{access_token:accessToken,session_id:pickerSession}})}}); const sj=await s.json(); if(s.ok){{say(sj.saved+'장 저장 완료');setTimeout(()=>location.reload(),700)}}else say(sj.error||'저장 실패'); return}}
  setTimeout(poll,3000);
}}
window.addEventListener('load',()=>{{if(!CLIENT_ID)return; document.getElementById('pickBtn').onclick=()=>{{const tc=google.accounts.oauth2.initTokenClient({{client_id:CLIENT_ID,scope:{json.dumps(SCOPE)},callback:(resp)=>{{if(resp.access_token)beginPicker(resp.access_token);else say('Google 승인 실패')}}}});tc.requestAccessToken({{prompt:'consent'}})}}}});
</script>'''
    return base.page('2026 발리 사진', body)

@app.route('/photos/bali-2026/file/<path:name>')
def bali_photo_file(name):
    return send_from_directory(PHOTO_DIR, name)

@app.route('/photos/picker/create', methods=['POST'])
def picker_create():
    token=(request.get_json(silent=True) or {}).get('access_token','')
    if not token:
        return jsonify(error='Google 인증 토큰이 없습니다.'),400
    r=requests.post('https://photospicker.googleapis.com/v1/sessions',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},json={},timeout=15)
    if not r.ok:
        return jsonify(error='Picker 세션 생성 실패',detail=r.text[:300]),r.status_code
    j=r.json(); return jsonify(id=j.get('id'),pickerUri=j.get('pickerUri'))

@app.route('/photos/picker/status', methods=['POST'])
def picker_status():
    d=request.get_json(silent=True) or {};token=d.get('access_token','');sid=d.get('session_id','')
    if not token or not sid:
        return jsonify(error='인증 정보가 부족합니다.'),400
    r=requests.get('https://photospicker.googleapis.com/v1/sessions/'+sid,headers={'Authorization':'Bearer '+token},timeout=15)
    if not r.ok:
        return jsonify(error='Picker 상태 확인 실패'),r.status_code
    return jsonify(ready=bool(r.json().get('mediaItemsSet')))

def _picked_items(token,sid):
    items=[];page=''
    while True:
        params={'sessionId':sid,'pageSize':100}
        if page:
            params['pageToken']=page
        r=requests.get('https://photospicker.googleapis.com/v1/mediaItems',headers={'Authorization':'Bearer '+token},params=params,timeout=20)
        r.raise_for_status();j=r.json();items.extend(j.get('mediaItems',[]));page=j.get('nextPageToken','')
        if not page:
            break
    return items

@app.route('/photos/picker/save', methods=['POST'])
def picker_save():
    d=request.get_json(silent=True) or {};token=d.get('access_token','');sid=d.get('session_id','')
    if not token or not sid:
        return jsonify(error='인증 정보가 부족합니다.'),400
    try:
        items=_picked_items(token,sid);saved=[]
        for idx,it in enumerate(items):
            mf=it.get('mediaFile') or {};mime=mf.get('mimeType','')
            if not mime.startswith('image/'):
                continue
            name=mf.get('filename') or f'photo-{idx+1}.jpg';safe=''.join(c if c.isalnum() or c in '._-' else '_' for c in name)
            if not safe:
                safe=f'photo-{idx+1}.jpg'
            url=(mf.get('baseUrl') or '')+'=w2048-h2048'
            rr=requests.get(url,headers={'Authorization':'Bearer '+token},timeout=30)
            rr.raise_for_status();(PHOTO_DIR/safe).write_bytes(rr.content)
            saved.append({'id':it.get('id',''),'file':safe,'name':name,'createTime':it.get('createTime','')})
        MANIFEST.write_text(json.dumps(saved,ensure_ascii=False,indent=2),'utf-8')
        try:
            requests.delete('https://photospicker.googleapis.com/v1/sessions/'+sid,headers={'Authorization':'Bearer '+token},timeout=10)
        except Exception:
            pass
        return jsonify(saved=len(saved))
    except Exception as e:
        return jsonify(error='사진 저장 실패',detail=str(e)[:300]),500
