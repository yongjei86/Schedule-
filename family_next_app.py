import json
import os
import threading
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Response, redirect
from pywebpush import webpush, WebPushException

import family_features_app as features
import home_cleanup_app as home
import pwa_app as pwa
import app as base

app = features.app
KST = ZoneInfo('Asia/Seoul')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '').strip()
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '').replace('\\n', '\n').strip()


# ===== schema =====
def init_next_schema():
    c = base.db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS push_subscriptions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      endpoint TEXT NOT NULL UNIQUE,
      p256dh TEXT NOT NULL,
      auth TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS push_log(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      subscription_id INTEGER NOT NULL,
      reminder_key TEXT NOT NULL,
      sent_at TEXT NOT NULL,
      UNIQUE(subscription_id, reminder_key)
    );
    ''')
    c.commit(); c.close()


init_next_schema()


# ===== shared UI / nav =====
base.CSS += '''
.person-tabs{display:flex;gap:6px;margin-bottom:12px}.person-tabs a{padding:8px 12px;border-radius:9px;text-decoration:none;background:#eaf0f6;color:#65758b;font-size:13px;font-weight:700}.person-tabs a.on{background:#0f4c81;color:#fff}.person-week{display:grid;grid-template-columns:repeat(7,minmax(145px,1fr));gap:8px;overflow-x:auto;padding-bottom:8px}.person-day{min-width:145px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:10px}.person-day.today{border:2px solid #0f4c81}.person-date{font-size:11px;color:#7b8797}.person-item{margin-top:7px;padding:8px;border-radius:9px;background:#f2f5f8;border-left:4px solid #7d8793;font-size:12px}.person-item.academy{background:#fff2eb;border-left-color:#e98755}.person-item.family{background:#fff7df;border-left-color:#c99a35}.person-item.trip{background:#fff0f1;border-left-color:#d64f5b}.notify-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:16px;max-width:680px}.notify-state{margin:10px 0;padding:10px;border-radius:10px;background:#f2f5f8}.auto-note{font-size:11px;color:#748196;margin-top:4px}
@media(max-width:700px){.person-week{grid-template-columns:repeat(7,minmax(138px,1fr))}.person-day{min-width:138px;padding:8px}}
'''


def next_nav():
    return ('<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b>'
            '<div class="nav">'
            '<a href="/past">과거 여행</a>'
            '<a href="/future">향후 여행</a>'
            '<a href="/calendar">가족 달력</a>'
            '<a href="/tasks">할 일</a>'
            '<a href="/kids">아이 일정</a>'
            '<a href="/notifications">알림</a>'
            '</div></nav></header>')


base.nav = next_nav
try:
    pwa._manifest['shortcuts'] = [x for x in pwa._manifest.get('shortcuts', []) if x.get('url') != '/riley']
    pwa._manifest['shortcuts'].append({'name':'아이 일정','short_name':'아이 일정','url':'/kids'})
    pwa._manifest['shortcuts'].append({'name':'알림 설정','short_name':'알림','url':'/notifications'})
except Exception:
    pass


# ===== child weekly schedules =====
def _person_events(person, mon, sun):
    rows=[]
    for raw in home._cached_calendar_events(mon, sun):
        e=dict(raw)
        compact=(e.get('title') or '').replace(' ','')
        if '청소아줌마' in compact:
            continue
        who=(e.get('person') or '').strip()
        title=(e.get('title') or '').strip()
        category=(e.get('category') or '').strip()
        source=e.get('source') or ''
        related=(person in who) or (person in title) or who=='가족' or category in ('공휴일','휴일')
        if source=='trip' and person in (who or ''):
            related=True
        if not related:
            continue
        try:
            sd=datetime.strptime(str(e.get('start_date') or '')[:10],'%Y-%m-%d').date()
            ed=datetime.strptime(str(e.get('end_date') or e.get('start_date') or '')[:10],'%Y-%m-%d').date()
        except Exception:
            continue
        d=max(sd,mon)
        while d<=min(ed,sun):
            rows.append({'date':d,'title':title or '(제목 없음)','meta':category or who or '가족','kind':'trip' if source=='trip' else 'family','time':''})
            d+=timedelta(days=1)

    if person=='지유':
        c=base.db(); academy=[dict(x) for x in c.execute('select * from academy where active=1 order by start_time,id').fetchall()]; c.close()
        for r in academy:
            day=(r.get('day_of_week') or '').strip()
            if day not in base.DAYS:
                continue
            d=mon+timedelta(days=base.DAYS.index(day))
            rows.append({'date':d,'title':r.get('academy') or '일정','meta':r.get('subject') or '지유 일정','kind':'academy','time':r.get('start_time') or ''})
    rows.sort(key=lambda x:(x['date'],x.get('time') or '99:99',x['title']))
    return rows


@app.route('/kids')
def kids_schedule():
    person=(base.request.args.get('person') or '지유').strip()
    if person not in ('지유','혜온'):
        person='지유'
    q=base.qdate(base.request.args.get('date','')) or date.today()
    mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6); today=date.today()
    rows=_person_events(person,mon,sun)
    by={mon+timedelta(days=i):[] for i in range(7)}
    for r in rows:
        by[r['date']].append(r)
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    tabs=(f'<div class="person-tabs"><a class="{"on" if person=="지유" else ""}" href="/kids?person=지유&date={q.isoformat()}">지유</a>'
          f'<a class="{"on" if person=="혜온" else ""}" href="/kids?person=혜온&date={q.isoformat()}">혜온</a></div>')
    nav=(f'<div class="riley-toolbar"><div><a class="btn s" href="/kids?person={base.H(person)}&date={prev}">← 이전 주</a> '
         f'<a class="btn s" href="/kids?person={base.H(person)}&date={today.isoformat()}">이번 주</a> '
         f'<a class="btn s" href="/kids?person={base.H(person)}&date={nxt}">다음 주 →</a></div>'
         f'<b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div>')
    body=tabs+nav+'<div class="person-week">'
    for i in range(7):
        d=mon+timedelta(days=i)
        body+=f'<div class="person-day {"today" if d==today else ""}"><div class="person-date">{d.strftime("%m/%d")}</div><h3>{base.DAYS[i]}</h3>'
        if not by[d]:
            body+='<div class="muted">일정 없음</div>'
        for r in by[d]:
            meta=(r.get('time')+' · ' if r.get('time') else '')+(r.get('meta') or '')
            body+=f'<div class="person-item {r["kind"]}"><b>{base.H(r["title"])}</b><div class="feature-meta">{base.H(meta)}</div></div>'
        body+='</div>'
    body+='</div>'
    return base.page(f'{person} 주간 일정',body)


# Keep old /riley links working, but direct users to the unified child schedule.
@app.route('/children')
def children_alias():
    return redirect('/kids')


# ===== automatic trip preparation checklist =====
AUTO_CHECKS = [
    (30,'서류','여권 유효기간 확인'),
    (30,'예약','주요 교통·숙소 예약 확인'),
    (30,'준비','여행자보험 검토'),
    (7,'준비','현지 날씨 확인 및 옷 준비'),
    (7,'아이','상비약·아이 준비물 점검'),
    (7,'결제','환전·해외 결제수단 점검'),
    (1,'체크인','온라인 체크인'),
    (1,'서류','여권·예약증 최종 확인'),
    (1,'짐','충전기·짐 최종 점검'),
]


def _ensure_auto_checklist(trip_id):
    c=base.db(); trip=c.execute('select id,start_date,status from trips where id=?',(trip_id,)).fetchone()
    if not trip:
        c.close(); return
    start=base.qdate(trip['start_date'] or '')
    if not start:
        c.close(); return
    existing={r['title'] for r in c.execute('select title from trip_checklist where trip_id=?',(trip_id,)).fetchall()}
    now=datetime.now().isoformat(timespec='seconds')
    for days_before,category,title in AUTO_CHECKS:
        auto_title='[자동] '+title
        if auto_title in existing:
            continue
        due=(start-timedelta(days=days_before)).isoformat()
        c.execute('insert into trip_checklist(trip_id,title,category,assignee,due_date,done,created_at) values(?,?,?,?,?,0,?)',
                  (trip_id,auto_title,category,'가족',due,now))
    c.commit(); c.close()


_original_trip_plan=None
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/trip/<int:trip_id>/plan':
        _original_trip_plan=app.view_functions[rule.endpoint]
        break

if _original_trip_plan:
    def trip_plan_with_auto(trip_id):
        _ensure_auto_checklist(trip_id)
        return _original_trip_plan(trip_id)
    for rule in list(app.url_map.iter_rules()):
        if rule.rule=='/trip/<int:trip_id>/plan':
            app.view_functions[rule.endpoint]=trip_plan_with_auto


# ===== web push =====
def _push_enabled():
    return bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)


@app.route('/push/public-key')
def push_public_key():
    return Response(json.dumps({'publicKey':VAPID_PUBLIC_KEY if _push_enabled() else ''}),mimetype='application/json')


@app.route('/push/subscribe',methods=['POST'])
def push_subscribe():
    if not _push_enabled():
        return Response(json.dumps({'ok':False,'error':'push_not_configured'}),status=503,mimetype='application/json')
    data=base.request.get_json(silent=True) or {}
    endpoint=(data.get('endpoint') or '').strip(); keys=data.get('keys') or {}
    p256dh=(keys.get('p256dh') or '').strip(); auth=(keys.get('auth') or '').strip()
    if not endpoint or not p256dh or not auth:
        return Response(json.dumps({'ok':False}),status=400,mimetype='application/json')
    c=base.db(); c.execute('insert into push_subscriptions(endpoint,p256dh,auth,created_at) values(?,?,?,?) on conflict(endpoint) do update set p256dh=excluded.p256dh,auth=excluded.auth',
                           (endpoint,p256dh,auth,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
    return Response(json.dumps({'ok':True}),mimetype='application/json')


@app.route('/notifications')
def notification_settings():
    configured='사용 가능' if _push_enabled() else '설정 필요'
    body=f'''<div class="notify-card"><h2>PWA 알림</h2>
<p>가족 일정과 여행 준비 마감이 가까워지면 설치된 앱으로 알림을 받을 수 있습니다.</p>
<div class="notify-state">서버 상태: <b>{configured}</b><br>알림 대상: 오늘/내일 가족 할 일 · 내일 가족 일정 · 여행 D-7/D-1 · 여행 준비 체크리스트</div>
<button class="btn" id="pushEnable" onclick="enableFamilyPush()">이 기기에서 알림 켜기</button>
<div id="pushResult" class="feature-meta" style="margin-top:8px"></div></div>
<script>
function b64ToUint8Array(base64String){{const padding='='.repeat((4-base64String.length%4)%4);const base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');const raw=atob(base64);return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)));}}
async function enableFamilyPush(){{
 const out=document.getElementById('pushResult');
 try{{
  if(!('serviceWorker' in navigator)||!('PushManager' in window)) throw new Error('이 브라우저는 푸시 알림을 지원하지 않습니다.');
  const perm=await Notification.requestPermission(); if(perm!=='granted') throw new Error('알림 권한이 허용되지 않았습니다.');
  const keyResp=await fetch('/push/public-key'); const keyData=await keyResp.json(); if(!keyData.publicKey) throw new Error('서버 알림 설정이 아직 준비되지 않았습니다.');
  const reg=await navigator.serviceWorker.ready;
  let sub=await reg.pushManager.getSubscription();
  if(!sub) sub=await reg.pushManager.subscribe({{userVisibleOnly:true,applicationServerKey:b64ToUint8Array(keyData.publicKey)}});
  const resp=await fetch('/push/subscribe',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(sub)}});
  if(!resp.ok) throw new Error('구독 저장에 실패했습니다.');
  out.textContent='알림이 켜졌습니다.';
 }}catch(e){{out.textContent=e.message||'알림 설정에 실패했습니다.';}}
}}
</script>'''
    return base.page('알림 설정',body)


# Add push handling to the existing service worker without changing its cache behavior.
pwa._SW += '''\nself.addEventListener('push',event=>{let data={};try{data=event.data?event.data.json():{};}catch(e){data={body:event.data?event.data.text():''};}const title=data.title||'우리 가족 기록';const options={body:data.body||'',icon:'/pwa-icon-v2.svg',badge:'/pwa-icon-v2.svg',data:{url:data.url||'/'}};event.waitUntil(self.registration.showNotification(title,options));});self.addEventListener('notificationclick',event=>{event.notification.close();const url=(event.notification.data&&event.notification.data.url)||'/';event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{for(const c of list){if('focus'in c){c.navigate(url);return c.focus();}}return clients.openWindow(url);}));});'''


def _subscriptions():
    c=base.db(); rows=[dict(x) for x in c.execute('select * from push_subscriptions').fetchall()]; c.close(); return rows


def _already_sent(sub_id,key):
    c=base.db(); r=c.execute('select 1 from push_log where subscription_id=? and reminder_key=?',(sub_id,key)).fetchone(); c.close(); return bool(r)


def _mark_sent(sub_id,key):
    c=base.db(); c.execute('insert or ignore into push_log(subscription_id,reminder_key,sent_at) values(?,?,?)',(sub_id,key,datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()


def _delete_subscription(sub_id):
    c=base.db(); c.execute('delete from push_subscriptions where id=?',(sub_id,)); c.execute('delete from push_log where subscription_id=?',(sub_id,)); c.commit(); c.close()


def _send_one(sub,title,body,url,key):
    if _already_sent(sub['id'],key):
        return
    info={'endpoint':sub['endpoint'],'keys':{'p256dh':sub['p256dh'],'auth':sub['auth']}}
    try:
        webpush(subscription_info=info,data=json.dumps({'title':title,'body':body,'url':url},ensure_ascii=False),vapid_private_key=VAPID_PRIVATE_KEY,vapid_claims={'sub':'mailto:family-app@example.com'},ttl=3600)
        _mark_sent(sub['id'],key)
    except WebPushException as e:
        status=getattr(getattr(e,'response',None),'status_code',None)
        if status in (404,410):
            _delete_subscription(sub['id'])
    except Exception as e:
        print(f'Push reminder failed: {type(e).__name__}',flush=True)


def _reminders_for(now):
    today=now.date(); tomorrow=today+timedelta(days=1); reminders=[]
    c=base.db()
    today_tasks=[dict(x) for x in c.execute("select * from family_tasks where done=0 and due_date=?",(today.isoformat(),)).fetchall()]
    tomorrow_tasks=[dict(x) for x in c.execute("select * from family_tasks where done=0 and due_date=?",(tomorrow.isoformat(),)).fetchall()]
    today_checks=[dict(x) for x in c.execute("select tc.*,t.title trip_title from trip_checklist tc join trips t on t.id=tc.trip_id where tc.done=0 and tc.due_date=?",(today.isoformat(),)).fetchall()]
    tomorrow_checks=[dict(x) for x in c.execute("select tc.*,t.title trip_title from trip_checklist tc join trips t on t.id=tc.trip_id where tc.done=0 and tc.due_date=?",(tomorrow.isoformat(),)).fetchall()]
    future=[dict(x) for x in c.execute("select id,title,start_date from trips where status!='완료' and start_date>=? order by start_date",(today.isoformat(),)).fetchall()]
    c.close()
    if 7<=now.hour<=10:
        if today_tasks:
            reminders.append(('오늘 할 일',f'{len(today_tasks)}건의 가족 할 일이 오늘 마감입니다.','/tasks',f'task-today-{today.isoformat()}'))
        if today_checks:
            reminders.append(('오늘 여행 준비',f'{len(today_checks)}건의 여행 준비 항목이 오늘 마감입니다.','/future',f'check-today-{today.isoformat()}'))
        for t in future:
            sd=base.qdate(t.get('start_date') or '')
            if not sd: continue
            left=(sd-today).days
            if left in (7,1):
                reminders.append((f'{t["title"]} D-{left}','여행 준비 체크리스트와 예약을 확인하세요.',f'/trip/{t["id"]}/plan',f'trip-{t["id"]}-d{left}'))
    if 18<=now.hour<=21:
        events=[]
        for e in home._cached_calendar_events(tomorrow,tomorrow):
            d=dict(e); compact=(d.get('title') or '').replace(' ','')
            if '청소아줌마' in compact: continue
            events.append(d)
        if events:
            reminders.append(('내일 가족 일정',f'{len(events)}건의 일정이 있습니다.','/calendar',f'events-tomorrow-{tomorrow.isoformat()}'))
        if tomorrow_tasks:
            reminders.append(('내일 마감 할 일',f'{len(tomorrow_tasks)}건의 가족 할 일이 내일 마감입니다.','/tasks',f'task-tomorrow-{tomorrow.isoformat()}'))
        if tomorrow_checks:
            reminders.append(('내일 여행 준비',f'{len(tomorrow_checks)}건의 여행 준비 항목이 내일 마감입니다.','/future',f'check-tomorrow-{tomorrow.isoformat()}'))
    return reminders


def push_loop():
    time.sleep(20)
    while True:
        try:
            if _push_enabled():
                now=datetime.now(KST)
                reminders=_reminders_for(now)
                if reminders:
                    for sub in _subscriptions():
                        for title,body,url,key in reminders:
                            _send_one(sub,title,body,url,key)
        except Exception as e:
            print(f'Push loop failed: {type(e).__name__}',flush=True)
        time.sleep(1800)


threading.Thread(target=push_loop,daemon=True,name='family-push-reminders').start()
