import json

from flask import Response

import home_cleanup_app as current
import app as base

app = current.app

PWA_NAME = '우리 가족 기록'
PWA_SHORT_NAME = '가족 기록'
PWA_THEME = '#0f4c81'
PWA_BG = '#f4f7fb'

_manifest = {
    'name': PWA_NAME,
    'short_name': PWA_SHORT_NAME,
    'description': '우리 가족의 여행, 일정, 지유 주간 일정을 한곳에서 관리합니다.',
    'start_url': '/',
    'scope': '/',
    'display': 'standalone',
    'orientation': 'any',
    'background_color': PWA_BG,
    'theme_color': PWA_THEME,
    'lang': 'ko-KR',
    'icons': [
        {'src': '/pwa-icon.svg', 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any maskable'},
    ],
    'shortcuts': [
        {'name': '가족 달력', 'short_name': '달력', 'url': '/calendar'},
        {'name': '지유 주간 일정', 'short_name': '지유 일정', 'url': '/riley'},
        {'name': '향후 여행', 'short_name': '향후 여행', 'url': '/future'},
    ],
}

_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="116" fill="#0f4c81"/>
<circle cx="390" cy="126" r="54" fill="#ffffff" opacity=".16"/>
<path d="M96 292c0-25 20-45 45-45h230c25 0 45 20 45 45v86c0 25-20 45-45 45H141c-25 0-45-20-45-45v-86z" fill="#ffffff" opacity=".96"/>
<path d="M165 247c9-72 51-121 91-121s82 49 91 121" fill="none" stroke="#ffffff" stroke-width="28" stroke-linecap="round"/>
<circle cx="190" cy="330" r="24" fill="#e98755"/>
<circle cx="256" cy="330" r="24" fill="#46a081"/>
<circle cx="322" cy="330" r="24" fill="#9a66ad"/>
<path d="M256 64l18 38 42 6-30 29 7 41-37-19-37 19 7-41-30-29 42-6 18-38z" fill="#f5c451"/>
</svg>'''

_SW = '''const CACHE='family-pwa-v1';
const SHELL=['/manifest.webmanifest','/pwa-icon.svg'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==location.origin) return;
  if(event.request.mode==='navigate'){
    event.respondWith(fetch(event.request).catch(()=>caches.match('/')));
    return;
  }
  if(url.pathname==='/manifest.webmanifest'||url.pathname==='/pwa-icon.svg'){
    event.respondWith(caches.match(event.request).then(r=>r||fetch(event.request).then(resp=>{const copy=resp.clone();caches.open(CACHE).then(c=>c.put(event.request,copy));return resp;})));
  }
});'''

@app.route('/manifest.webmanifest')
def pwa_manifest():
    return Response(json.dumps(_manifest, ensure_ascii=False), mimetype='application/manifest+json', headers={'Cache-Control':'public, max-age=3600'})

@app.route('/pwa-icon.svg')
def pwa_icon():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'public, max-age=86400'})

@app.route('/service-worker.js')
def pwa_service_worker():
    return Response(_SW, mimetype='application/javascript', headers={'Cache-Control':'no-cache','Service-Worker-Allowed':'/'})

_original_page = base.page

def pwa_page(title, body):
    html = _original_page(title, body)
    pwa_head = f'''<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="{PWA_THEME}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="{PWA_SHORT_NAME}">
<link rel="icon" href="/pwa-icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/pwa-icon.svg">'''
    pwa_script = '''<script>if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(()=>{}));}</script>'''
    return html.replace('</head>', pwa_head + '</head>').replace('</body>', pwa_script + '</body>')

base.page = pwa_page
