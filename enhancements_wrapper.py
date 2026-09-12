import os, json
from datetime import datetime, date, timedelta, time as dtime
from zoneinfo import ZoneInfo
import requests
from icalendar import Calendar
import recurring_ical_events
import photos_wrapper as photos
import gcal_wrapper as gcal
import app as base

app = photos.app
KST = ZoneInfo('Asia/Seoul')

base.CSS += '''
.homegrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px}.dashcard{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:14px}.dashcard h3{margin:0 0 8px}.big{font-size:28px;font-weight:900;color:#0f4c81}.muted{color:#718097;font-size:12px}.tripdetail{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.timeline{display:grid;gap:8px}.tl{display:grid;grid-template-columns:110px 1fr;gap:10px;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px}.triplink{color:#0f4c81;text-decoration:none;font-weight:800}.searchbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}.searchbar input,.searchbar select{max-width:220px}.mapbox{height:520px;border-radius:16px;overflow:hidden;border:1px solid #e4e9f0;background:#eef3f7}.statgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.stat{background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:12px;text-align:center}.stat b{display:block;font-size:22px;color:#0f4c81}.sectiontitle{margin:22px 0 8px}.quicklinks{display:flex;gap:8px;flex-wrap:wrap}.quicklinks a{text-decoration:none}
@media(max-width:900px){.homegrid,.tripdetail,.statgrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.homegrid,.tripdetail,.statgrid{grid-template-columns:1fr}.tl{grid-template-columns:90px 1fr}.mapbox{height:420px}}
'''

def new_nav():
    return '<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b><div class="nav"><a href="/">홈</a><a href="/past">과거 여행</a><a href="/future">향후 여행</a><a href="/travel-map">여행 지도</a><a href="/travel-search">검색</a><a href="/calendar">가족 달력</a><a href="/riley">지유 주간 일정</a>'+('<a href="/logout">로그아웃</a>' if base.admin() else '<a href="/login">관리자</a>')+'</div></nav></header>'
base.nav = new_nav

# Add trips to the family calendar without duplicating them in calendar_events.
_prev_event_rows = base.event_rows

def event_rows_with_trips(start, end):
    rows = list(_prev_event_rows(start, end))
    c = base.db()
    trips = c.execute('select * from trips where start_date<=? and end_date>=? order by start_date,id',(end.isoformat(),start.isoformat())).fetchall()
    c.close()
    for r in trips:
        rows.append({'id':'trip:'+str(r['id']),'start_date':r['start_date'],'end_date':r['end_date'],'title':r['title'],'category':'여행','person':r['companions'],'notes':r['region'],'source':'trip','trip_id':r['id']})
    rows.sort(key=lambda x:(x['start_date'],x['title']))
    return rows
base.event_rows = event_rows_with_trips

def event_modals_with_trip(es):
    b=''
    for e in es:
        d=dict(e)
        source=d.get('source','local')
        title=base.H(d.get('title',''))
        if source=='trip':
            title=f'<a class="triplink" href="/trip/{d.get("trip_id")}">{title}</a>'
        badge = '<span class="pill">Google</span> ' if source=='google' else ('<span class="pill">여행</span> ' if source=='trip' else '')
        a=''
        if source=='local' and base.admin():
            dat=' '.join('data-'+k+'="'+base.H(d.get(k,''))+'"' for k in ['id','start_date','end_date','title','category','person','notes'])
            a=f'<div><button class="btn s" {dat} onclick="ee(this)">수정</button><form method="post" action="/event/{d["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
        b += f'<div class="event"><div><b>{base.H(d.get("start_date"))} ~ {base.H(d.get("end_date"))}</b> · {title} {badge}<span class="pill">{base.H(d.get("category"))}</span><br>{base.H(d.get("person"))} · {base.H(d.get("notes"))}</div>{a}</div>'
    if base.admin():
        b += '''<div class="modal" id="em"><div class="card"><div class="head"><h2>가족 일정</h2><button class="btn s" onclick="x('em')">닫기</button></div><form class="form" id="ef" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label class="full">일정명<input name="title" required></label><label>분류<input name="category"></label><label>사람<input name="person"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
    return b
base.event_modals = event_modals_with_trip

# Make trip titles link to a dedicated detail page.
_prev_travels = base.travels

def travels_with_links(done):
    out = _prev_travels(done)
    c=base.db(); rows=c.execute("select id,title from trips where status"+("='완료'" if done else "!='완료'")+" order by start_date desc").fetchall(); c.close()
    for r in rows:
        old='<td><b>'+base.H(r['title'])+'</b>'
        new='<td><b><a class="triplink" href="/trip/'+str(r['id'])+'" onclick="event.stopPropagation()">'+base.H(r['title'])+'</a></b>'
        out=out.replace(old,new,1)
    return out
base.travels = travels_with_links


def _timed_google(start,end,name='지유'):
    out=[]
    srcs=[s for s in gcal._sources() if s.get('name')==name]
    ws=datetime.combine(start,dtime.min,tzinfo=KST); we=datetime.combine(end+timedelta(days=1),dtime.min,tzinfo=KST)
    for src in srcs:
        try:
            r=requests.get(src['url'],timeout=10,headers={'User-Agent':'YJ-Family-Calendar/1.0'}); r.raise_for_status()
            cal=Calendar.from_ical(r.content)
            for ev in recurring_ical_events.of(cal).between(ws,we):
                if str(ev.get('STATUS','')).upper()=='CANCELLED': continue
                ds=ev.decoded('DTSTART') if ev.get('DTSTART') else None
                de=ev.decoded('DTEND') if ev.get('DTEND') else ds
                if not isinstance(ds,datetime): continue
                if ds.tzinfo: ds=ds.astimezone(KST)
                if isinstance(de,datetime) and de.tzinfo: de=de.astimezone(KST)
                day=ds.date()
                if not(start<=day<=end): continue
                out.append({'date':day,'start':ds.strftime('%H:%M'),'end':de.strftime('%H:%M') if isinstance(de,datetime) else '', 'title':str(ev.get('SUMMARY','(제목 없음)')),'location':str(ev.get('LOCATION','') or '')})
        except Exception as e:
            print('Riley Google timetable sync failed:',e,flush=True)
    return out


def riley_week():
    q=base.qdate(base.request.args.get('date','')) or date.today()
    mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6)
    ge=_timed_google(mon,sun,'지유')
    by={mon+timedelta(days=i):[] for i in range(7)}
    for x in ge: by[x['date']].append(x)
    c=base.db(); local=c.execute('select * from academy where active=1 order by start_time,id').fetchall(); c.close()
    for i,dayname in enumerate(base.DAYS):
        d=mon+timedelta(days=i); existing={(x['title'],x['start']) for x in by[d]}
        for r in local:
            if r['day_of_week']!=dayname: continue
            key=(r['academy'],r['start_time'] or '')
            if key in existing: continue
            by[d].append({'date':d,'start':r['start_time'] or '시간 미정','end':r['end_time'] or '','title':r['academy'],'location':r['location'] or '', 'local_id':r['id'], 'notes':r['notes'] or ''})
        by[d].sort(key=lambda x:x['start'])
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    body=f'<div class="toolbar"><div><a class="btn s" href="/riley?date={prev}">← 이전 주</a> <a class="btn s" href="/riley?date={nxt}">다음 주 →</a></div><b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div><div class="schedule">'
    for i,d in enumerate(by):
        body+=f'<div class="sday"><div class="date">{d.strftime("%m/%d")}</div><h3>{base.DAYS[i]}</h3>'
        if not by[d]: body+='<div class="muted">일정 없음</div>'
        for x in by[d]:
            tm=x['start']+(("–"+x['end']) if x.get('end') else '')
            body+=f'<div class="lesson"><b>{base.H(x["title"])}</b>{base.H(tm)}'+(f'<br><span class="muted">{base.H(x.get("location"))}</span>' if x.get('location') else '')+'</div>'
        if base.admin(): body+=f'<button class="btn s" onclick="na(\'{base.DAYS[i]}\')">+ 일정</button>'
        body+='</div>'
    body+='</div><p class="muted" style="margin-top:10px">지유 Google Calendar의 시간 일정이 우선 표시되고, 기존 학원 DB 일정은 빠진 항목만 보완합니다.</p>'
    return base.page('지유 주간 일정',body)

# Replace the existing /riley handler regardless of its function name.
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/riley':
        app.view_functions[rule.endpoint]=riley_week

@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    c=base.db(); r=c.execute('select * from trips where id=?',(trip_id,)).fetchone(); its=c.execute('select * from itinerary where trip_id=? order by sort_order,item_date,id',(trip_id,)).fetchall(); c.close()
    if not r: return base.abort(404)
    meta=f'''<div class="tripdetail"><div class="dashcard"><span class="muted">여행 일자</span><h3>{base.H(r['start_date'])} ~ {base.H(r['end_date'])}</h3></div><div class="dashcard"><span class="muted">지역</span><h3>{base.H(r['country'])} · {base.H(r['region'])}</h3></div><div class="dashcard"><span class="muted">함께</span><h3>{base.H(r['companions'])}</h3></div><div class="dashcard"><span class="muted">숙소</span><h3>{base.H(r['lodging']) or '-'}</h3></div><div class="dashcard"><span class="muted">교통/항공</span><h3>{base.H(r['transport']) or '-'}</h3></div><div class="dashcard"><span class="muted">상태</span><h3>{base.H(r['status'])}</h3></div></div>'''
    tl='<h2 class="sectiontitle">일자별 일정</h2><div class="timeline">'
    if not its: tl+='<div class="dashcard muted">아직 세부 일정이 없습니다.</div>'
    for x in its:
        left=' · '.join(v for v in [x['item_date'],x['day_label'],x['time_text']] if v)
        tl+=f'<div class="tl"><div><b>{base.H(left)}</b></div><div><b>{base.H(x["title"])}</b>'+(f'<br>{base.H(x["place"])}' if x['place'] else '')+(f'<br><span class="muted">{base.H(x["detail"])}</span>' if x['detail'] else '')+'</div></div>'
    tl+='</div>'
    extra=f'<h2 class="sectiontitle">메모</h2><div class="dashcard">{base.H(r["notes"]) or "-"}</div>'
    if r['start_date']=='2026-08-08' and '발리' in (r['title'] or ''):
        extra+= '<div class="quicklinks" style="margin-top:12px"><a class="btn" href="/photos/bali-2026">📷 발리 사진 갤러리</a></div>'
    return base.page(r['title'],f'<div class="toolbar"><a class="btn s" href="/past">← 여행 목록</a></div>'+meta+tl+extra)

@app.route('/travel-search')
def travel_search():
    q=(base.request.args.get('q') or '').strip(); status=(base.request.args.get('status') or '').strip(); kind=(base.request.args.get('kind') or '').strip()
    c=base.db(); rows=c.execute('select * from trips order by start_date desc').fetchall(); c.close()
    def ok(r):
        text=' '.join(str(r[k] or '') for k in ['country','region','title','companions','lodging','notes'])
        return (not q or q.lower() in text.lower()) and (not status or r['status']==status) and (not kind or r['trip_type']==kind)
    rows=[r for r in rows if ok(r)]
    body=f'''<form class="searchbar" method="get"><input name="q" placeholder="국가·도시·여행명 검색" value="{base.H(q)}"><select name="kind"><option value="">국내/해외 전체</option><option {'selected' if kind=='해외' else ''}>해외</option><option {'selected' if kind=='국내' else ''}>국내</option></select><select name="status"><option value="">상태 전체</option>'''
    for s in ['완료','예정','검토 중','장기 계획']: body+=f'<option {"selected" if status==s else ""}>{s}</option>'
    body+='</select><button class="btn">검색</button></form>'
    body+=f'<div class="box"><table><tr><th>일자</th><th>국가</th><th>지역</th><th>여행명</th><th>상태</th></tr>'
    for r in rows: body+=f'<tr><td>{base.H(r["start_date"])}</td><td>{base.H(r["country"])}</td><td>{base.H(r["region"])}</td><td><a class="triplink" href="/trip/{r["id"]}">{base.H(r["title"])}</a></td><td>{base.H(r["status"])}</td></tr>'
    body+='</table></div>'
    return base.page('여행 검색',body)

COUNTRY_COORDS={
'한국':(36.5,127.8),'대한민국':(36.5,127.8),'일본':(36.2,138.3),'대만':(23.7,121.0),'홍콩':(22.32,114.17),'마카오':(22.20,113.55),'중국':(35.9,104.2),'태국':(15.9,100.9),'베트남':(16.0,108.2),'인도네시아':(-2.5,118.0),'미국':(39.8,-98.6),'스페인':(40.4,-3.7),'이탈리아':(42.8,12.8),'싱가포르':(1.35,103.82),'호주':(-25.3,133.8),'체코':(49.8,15.5),'오스트리아':(47.5,14.5),'헝가리':(47.2,19.5)
}

def _country_parts(s):
    if not s: return []
    for sep in ['·','/','+','&',',']:
        s=s.replace(sep,'|')
    return [x.strip() for x in s.split('|') if x.strip()]

@app.route('/travel-map')
def travel_map():
    c=base.db(); rows=c.execute("select id,country,region,title,start_date from trips where status='완료' order by start_date").fetchall(); c.close()
    pins=[]
    for r in rows:
        for p in _country_parts(r['country']):
            key=p
            if key in COUNTRY_COORDS:
                lat,lon=COUNTRY_COORDS[key];pins.append({'lat':lat,'lon':lon,'country':key,'title':r['title'],'region':r['region'],'id':r['id'],'date':r['start_date']})
    data=json.dumps(pins,ensure_ascii=False)
    body=f'''<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><div id="map" class="mapbox"></div><p class="muted">완료된 가족 여행의 국가를 지도에 표시합니다. 핀을 누르면 여행 상세로 이동할 수 있어요.</p><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>const pins={data};const m=L.map('map').setView([25,35],2);L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:18,attribution:'&copy; OpenStreetMap'}}).addTo(m);pins.forEach(p=>L.marker([p.lat,p.lon]).addTo(m).bindPopup(`<b>${{p.title}}</b><br>${{p.date}} · ${{p.region||p.country}}<br><a href="/trip/${{p.id}}">여행 상세</a>`));</script>'''
    return base.page('우리 가족 여행 지도',body)


def dashboard():
    today=date.today(); c=base.db(); trips=c.execute('select * from trips order by start_date').fetchall(); done=[r for r in trips if r['status']=='완료']; future=[r for r in trips if r['status']!='완료' and base.qdate(r['start_date']) and base.qdate(r['start_date'])>=today]; c.close()
    nxt=future[0] if future else None
    dday=(base.qdate(nxt['start_date'])-today).days if nxt else None
    countries=set()
    for r in done:
        countries.update(_country_parts(r['country']))
    overseas=sum(1 for r in done if r['trip_type']=='해외')
    domestic=sum(1 for r in done if r['trip_type']=='국내')
    nextcard='<div class="dashcard"><h3>다음 여행</h3><div class="muted">등록된 예정 여행 없음</div></div>'
    if nxt:
        nextcard=f'<div class="dashcard"><h3>다음 여행</h3><div class="big">D-{dday}</div><a class="triplink" href="/trip/{nxt["id"]}">{base.H(nxt["title"])}</a><div class="muted">{base.H(nxt["start_date"])} · {base.H(nxt["region"])}</div></div>'
    calcard='<div class="dashcard"><h3>이번 주 가족 일정</h3><div class="muted">관리자 로그인 후 확인</div></div>'
    rileycard='<div class="dashcard"><h3>지유 주간 일정</h3><div class="muted">관리자 로그인 후 확인</div></div>'
    if base.admin():
        mon=today-timedelta(days=today.weekday()); sun=mon+timedelta(days=6); ev=base.event_rows(mon,sun)[:5]
        calcard='<div class="dashcard"><h3>이번 주 가족 일정</h3>'+(''.join(f'<div style="margin:6px 0"><b>{base.H(x["start_date"])}</b> · {base.H(x["title"])}</div>' for x in ev) if ev else '<div class="muted">일정 없음</div>')+'<a class="btn s" href="/calendar">달력 보기</a></div>'
        rileycard='<div class="dashcard"><h3>지유 주간 일정</h3><a class="btn s" href="/riley">시간표 보기</a></div>'
    body='<div class="homegrid">'+nextcard+calcard+rileycard+'</div>'
    body+=f'<div class="statgrid"><div class="stat"><b>{len(done)}</b><span class="muted">완료 여행</span></div><div class="stat"><b>{len(countries)}</b><span class="muted">방문 국가</span></div><div class="stat"><b>{overseas}</b><span class="muted">해외 여행</span></div><div class="stat"><b>{domestic}</b><span class="muted">국내 여행</span></div></div>'
    body+='<h2 class="sectiontitle">바로가기</h2><div class="quicklinks"><a class="btn" href="/future">향후 여행</a><a class="btn s" href="/travel-map">여행 지도</a><a class="btn s" href="/travel-search">여행 검색</a><a class="btn s" href="/photos/bali-2026">2026 발리 사진</a></div>'
    return base.page('우리 가족 기록',body)

# Replace the old root redirect with the dashboard.
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=dashboard
