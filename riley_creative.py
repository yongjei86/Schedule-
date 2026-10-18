"""Riley's region-based art studio and journal; shares the existing family DB."""
import json, re, secrets
from contextlib import contextmanager
from flask import render_template, request, session, jsonify, abort
import home_tasks_only_app as main
app = main.app

@contextmanager
def connection():
    c = main.db()
    try:
        with c:
            yield c
    finally:
        c.close()

with connection() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS riley_art(id TEXT PRIMARY KEY, title TEXT NOT NULL, colors TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0, updated TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS riley_journal(day TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, art_id TEXT, updated TEXT NOT NULL);''')

def now():
    return main.datetime.now(main.KST).isoformat(timespec='seconds')

def token():
    if 'creative_token' not in session: session['creative_token'] = secrets.token_hex(24)
    return session['creative_token']

def verify():
    if not secrets.compare_digest(request.headers.get('X-Creative-Token',''), session.get('creative_token','!')): abort(403)
    if request.content_length and request.content_length > 100000: abort(413)

@app.route('/riley/coloring')
@app.route('/riley/diary')
def riley_creative_page():
    response = main.Response(render_template('riley-creative.html', token=token(), diary=request.path.endswith('/diary')))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/riley/creative/data')
def riley_creative_data():
    with connection() as c:
        arts = [dict(r) for r in c.execute('SELECT * FROM riley_art ORDER BY updated DESC')]
        entries = [dict(r) for r in c.execute('SELECT * FROM riley_journal ORDER BY day DESC')]
    for art in arts: art['colors'] = json.loads(art['colors'])
    response = jsonify(arts=arts, entries=entries)
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.post('/riley/creative/art')
def riley_creative_art():
    verify(); data = request.get_json() or {}
    ident = data.get('id') or secrets.token_hex(12)
    if not isinstance(ident,str) or not re.fullmatch(r'[a-f0-9]{24}',ident): abort(400)
    colors = data.get('colors',{})
    if not isinstance(colors,dict) or len(colors)>1500: abort(400)
    if any(not re.fullmatch(r'[a-z0-9-]{1,50}',str(k)) or not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v) for k,v in colors.items()): abort(400)
    title = str(data.get('title') or '나의 해바라기')[:100]
    with connection() as c:
        c.execute('INSERT INTO riley_art VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,colors=excluded.colors,completed=excluded.completed,updated=excluded.updated', (ident,title,json.dumps(colors),int(bool(data.get('completed'))),now()))
    return jsonify(id=ident)

@app.post('/riley/creative/diary')
def riley_creative_diary():
    verify(); data = request.get_json() or {}; day = data.get('day','')
    if not isinstance(day,str) or not main.qdate(day): abort(400)
    title, body = str(data.get('title',''))[:200], str(data.get('body',''))[:20000]
    art = data.get('art_id') or None
    with connection() as c:
        if art and not c.execute('SELECT 1 FROM riley_art WHERE id=? AND completed=1',(art,)).fetchone(): abort(400)
        c.execute('INSERT INTO riley_journal VALUES(?,?,?,?,?) ON CONFLICT(day) DO UPDATE SET title=excluded.title,body=excluded.body,art_id=excluded.art_id,updated=excluded.updated',(day,title,body,art,now()))
    return jsonify(ok=True)

_old_reading = main._reading_section
def reading_with_creative(child='지유',base='/riley'):
    cards = ''
    if child=='지유' and base=='/riley':
        cards = '<section class="feature-card" style="margin:14px 0;padding:18px"><h2>지유의 창작 공간</h2><div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn" href="/riley/coloring">🌻 명화 색칠공부</a><a class="btn s" href="/riley/diary">📖 나의 일기장</a></div></section>'
    return cards + _old_reading(child,base)
main._reading_section = reading_with_creative
