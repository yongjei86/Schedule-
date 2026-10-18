import importlib, sys, types, io
from flask import Flask, Response, send_file

main=types.ModuleType('riley_creative')
main.app=Flask(__name__)
sys.modules['riley_creative']=main
mod=importlib.import_module('kids_touch')
app=main.app
page='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script src="/local-canvas.js"></script></head><body><canvas id="paint" style="touch-action:none"></canvas></body></html>'
for path in ['/riley','/riley/coloring','/riley/fashion','/riley/diary','/hyeon','/hyeon/coloring','/hyeon/hangul','/hyeon/dressup','/hyeon/princess','/hyeon/reading/dashboard','/calendar','/riley-other']:
    app.add_url_rule(path,path,lambda:Response(page,mimetype='text/html'))
@app.get('/static/hyeon-princess.html')
def static_html():
    return send_file(io.BytesIO(page.encode()),mimetype='text/html',download_name='princess.html')
@app.get('/riley/data')
def data():return {'ok':True}
client=app.test_client()
for path in ['/riley','/riley/coloring','/riley/fashion','/riley/diary','/hyeon','/hyeon/coloring','/hyeon/hangul','/hyeon/dressup','/hyeon/princess','/hyeon/reading/dashboard','/static/hyeon-princess.html']:
    r=client.get(path)
    assert r.status_code==200
    assert r.text.count('name="viewport"')==1,path
    assert 'maximum-scale=1' in r.text and 'user-scalable=no' in r.text,path
    assert r.text.index('charset=')<r.text.index('kids-page-zoom-lock')<r.text.index('/local-canvas.js')
    assert 'touch-action:none' in r.text
    assert r.headers['Cache-Control']=='no-store'
for path in ['/calendar','/riley-other']:
    assert 'kids-page-zoom-lock' not in client.get(path).text
assert client.get('/riley/data').json=={'ok':True}
variants=["<META NAME='viewport' CONTENT='initial-scale=1'>",'<meta content="initial-scale=1" name=viewport>']
for viewport in variants:
    with app.test_request_context('/riley'):
        r=mod.kids_fixed_page_viewport(Response('<html><head>'+viewport+'</head><body></body></html>',mimetype='text/html'))
        markup=r.get_data(as_text=True)
        assert markup.count('name="viewport"')==1
        assert 'initial-scale=1\'' not in markup
        assert '<meta charset="utf-8">' in markup
print('PASS: all Riley/Hyeon HTML pages, send_file pages, viewport uniqueness, native zoom restrictions, canvas gesture preservation, unchanged adult pages and JSON')
