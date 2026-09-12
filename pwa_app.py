import json

from flask import Response

import home_cleanup_app as current
import app as base

app = current.app

PWA_NAME = '우리 가족 기록'
PWA_SHORT_NAME = '가족 기록'
PWA_THEME = '#10253f'
PWA_BG = '#f4f7fb'
PWA_ICON = '/pwa-icon-v2.svg'

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
        {'src': PWA_ICON, 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any maskable'},
    ],
    'shortcuts': [
        {'name': '가족 달력', 'short_name': '달력', 'url': '/calendar'},
        {'name': '지유 주간 일정', 'short_name': '지유 일정', 'url': '/riley'},
        {'name': '향후 여행', 'short_name': '향후 여행', 'url': '/future'},
    ],
}

# Clean travel mark: deep navy tile + ivory globe + warm gold airplane.
# The important artwork stays inside the maskable safe area so Android/Samsung launchers
# can crop it to circles, squircles or rounded squares without losing details.
_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs>
  <linearGradient id="bg" x1="72" y1="54" x2="438" y2="462" gradientUnits="userSpaceOnUse">
    <stop stop-color="#183A60"/>
    <stop offset="1" stop-color="#0B1D32"/>
  </linearGradient>
</defs>
<rect width="512" height="512" rx="120" fill="url(#bg)"/>
<circle cx="256" cy="256" r="146" fill="#F8F5ED"/>
<circle cx="256" cy="256" r="106" fill="none" stroke="#B9C4CE" stroke-width="12"/>
<path d="M154 256h204M256 150c-31 30-48 67-48 106s17 76 48 106M256 150c31 30 48 67 48 106s-17 76-48 106" fill="none" stroke="#B9C4CE" stroke-width="12" stroke-linecap="round"/>
<path d="M174 200c25 13 53 19 82 19s57-6 82-19M174 312c25-13 53-19 82-19s57 6 82 19" fill="none" stroke="#B9C4CE" stroke-width="10" stroke-linecap="round"/>
<path d="M126 303c38-28 86-48 142-57l91-58c8-5 18-3 23 5 5 7 4 16-2 22l-69 64 50 11c10 2 17 11 16 21-1 9-9 16-18 17l-74 4-41 66c-5 8-15 11-23 7-8-4-12-13-9-22l23-69c-42 3-78 10-111 22-12 4-24-3-27-15-2-7 1-14 9-18z" fill="#D7A347"/>
<path d="M318 218l42-27" stroke="#FFF9EC" stroke-width="9" stroke-linecap="round"/>
<circle cx="116" cy="118" r="10" fill="#D7A347"/>
<circle cx="396" cy="394" r="7" fill="#D7A347" opacity=".75"/>
</svg>'''

_SW = '''const CACHE='family-pwa-v2';
const SHELL=['/manifest.webmanifest','/pwa-icon-v2.svg'];
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
  if(url.pathname==='/manifest.webmanifest'||url.pathname==='/pwa-icon-v2.svg'){
    event.respondWith(fetch(event.request).then(resp=>{const copy=resp.clone();caches.open(CACHE).then(c=>c.put(event.request,copy));return resp;}).catch(()=>caches.match(event.request)));
  }
});'''

@app.route('/manifest.webmanifest')
def pwa_manifest():
    return Response(json.dumps(_manifest, ensure_ascii=False), mimetype='application/manifest+json', headers={'Cache-Control':'no-cache'})

@app.route('/pwa-icon-v2.svg')
def pwa_icon_v2():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'public, max-age=86400'})

# Keep old route alive so previously installed versions do not break while updating.
@app.route('/pwa-icon.svg')
def pwa_icon_legacy():
    return Response(_ICON_SVG, mimetype='image/svg+xml', headers={'Cache-Control':'no-cache'})

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
<link rel="icon" href="{PWA_ICON}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{PWA_ICON}">'''
    pwa_script = '''<script>if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(()=>{}));}</script>'''
    return html.replace('</head>', pwa_head + '</head>').replace('</body>', pwa_script + '</body>')

base.page = pwa_page
