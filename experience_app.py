from datetime import date, timedelta, datetime
from collections import Counter, defaultdict

import main_app as main
import app as base

app = main.app

base.CSS += '''
.home-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-bottom:16px}.home-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px}.home-card h2{font-size:16px;margin:0 0 10px}.home-list{display:grid;gap:7px}.home-item{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #edf1f5}.home-item:last-child{border-bottom:0}.home-link{color:#14263f;text-decoration:none}.home-link:hover{text-decoration:underline}.quick-row{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 16px}.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.stat-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:13px}.stat-card .big{font-size:24px;font-weight:800;margin-top:4px}.bar-list{display:grid;gap:8px}.bar-row{display:grid;grid-template-columns:130px 1fr 45px;gap:9px;align-items:center}.bar-track{height:9px;background:#edf2f7;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:#0f4c81;border-radius:999px}.search-form{display:flex;gap:8px;margin-bottom:14px}.search-form input{flex:1}.search-result{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px;margin-bottom:8px}.search-result h3{margin:0 0 5px;font-size:15px}.search-meta{font-size:12px;color:#728096}.section-title{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:18px 0 9px}.section-title h2{margin:0;font-size:18px}
@media(max-width:700px){.home-grid{grid-template-columns:1fr}.stat-grid{grid-template-columns:repeat(2,1fr)}.bar-row{grid-template-columns:90px 1fr 36px}.search-form{flex-direction:column}}
'''


def _safe_date(s):
    try:
        return datetime.strptime((s or '')[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def _trip_days(r):
    a=_safe_date(r['start_date']); b=_safe_date(r['end_date'])
    if not a or not b or b<a:
        return 0
    return (b-a).days+1


def _next_trip(c, today):
    return c.execute("select * from trips where start_date>=? and status!='완료' order by start_date asc limit 1",(today.isoformat(),)).fetchone()


def _recent_trips(c):
    return c.execute("select * from trips where status='완료' order by end_date desc,start_date desc limit 4").fetchall()


def family_home():
    today=date.today(); month_start=today.replace(day=1)
    if today.month==12:
        month_end=date(today.year,12,31)
    else:
        month_end=date(today.year,today.month+1,1)-timedelta(days=1)
    week_start=today-timedelta(days=today.weekday()); week_end=week_start+timedelta(days=6)

    c=base.db(); nxt=_next_trip(c,today); recent=_recent_trips(c); completed=c.execute("select count(*) n from trips where status='완료'").fetchone()['n']; c.close()
    month_events=main.family_events(month_start,month_end)
    week_riley=main.recurring_riley_events(week_start,week_end,'지유')

    quick='<div class="quick-row"><a class="btn" href="/travel-search">통합 검색</a><a class="btn s" href="/travel-stats">여행 통계</a><a class="btn s" href="/calendar">가족 달력</a><a class="btn s" href="/riley">지유 주간 일정</a></div>'
    body=quick+'<div class="home-grid">'

    body+='<section class="home-card"><h2>다음 여행</h2>'
    if nxt:
        d=_safe_date(nxt['start_date']); dd=(d-today).days if d else None
        body+=f'<a class="home-link" href="/trip/{nxt["id"]}"><b>{base.H(nxt["title"])}</b></a><div style="margin-top:6px">{base.H(nxt["start_date"])} ~ {base.H(nxt["end_date"])}</div><div class="muted">{base.H(nxt["country"])} · {base.H(nxt["region"])}'+(f' · D-{dd}' if dd is not None and dd>=0 else '')+'</div>'
    else:
        body+='<div class="muted">예정된 여행이 없습니다.</div>'
    body+='</section>'

    body+=f'<section class="home-card"><h2>{today.month}월 가족 일정</h2><div class="home-list">'
    month_sorted=sorted(month_events,key=lambda e:(str(dict(e).get('start_date') or ''),str(dict(e).get('title') or '')))
    upcoming=[e for e in month_sorted if str(dict(e).get('end_date') or dict(e).get('start_date') or '')[:10]>=today.isoformat()][:6]
    if not upcoming:
        body+='<div class="muted">남은 일정이 없습니다.</div>'
    for e in upcoming:
        d=dict(e); body+=f'<div class="home-item"><span>{base.H(d.get("title"))}</span><span class="muted">{base.H(str(d.get("start_date") or "")[:10])}</span></div>'
    body+='</div></section>'

    body+='<section class="home-card"><h2>지유 이번주 일정</h2><div class="home-list">'
    if not week_riley:
        body+='<div class="muted">반복 학원 일정이 없습니다.</div>'
    for e in week_riley[:8]:
        body+=f'<div class="home-item"><span>{base.H(e["title"])}</span><span class="muted">{e["date"].strftime("%m/%d")} {base.H(e["start"])}</span></div>'
    body+='</div></section>'

    body+=f'<section class="home-card"><h2>최근 여행</h2><div class="muted" style="margin-bottom:5px">완료 여행 {completed}건</div><div class="home-list">'
    for r in recent:
        body+=f'<div class="home-item"><a class="home-link" href="/trip/{r["id"]}">{base.H(r["title"])}</a><span class="muted">{base.H((r["start_date"] or "")[:4])}</span></div>'
    body+='</div></section></div>'
    return base.page('우리 가족 기록',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=family_home
        break


@app.route('/travel-stats')
def travel_stats():
    c=base.db(); rows=c.execute("select * from trips where status='완료' order by start_date").fetchall(); c.close()
    total=len(rows); overseas=sum(1 for r in rows if (r['trip_type'] or '')=='해외'); domestic=sum(1 for r in rows if (r['trip_type'] or '')=='국내'); days=sum(_trip_days(r) for r in rows)
    country=Counter((r['country'] or '미분류').strip() or '미분류' for r in rows if (r['trip_type'] or '')=='해외')
    years=Counter((r['start_date'] or '')[:4] for r in rows if (r['start_date'] or '')[:4])
    companions=Counter((r['companions'] or '미분류').strip() or '미분류' for r in rows)
    body=f'<div class="stat-grid"><div class="stat-card"><div class="muted">완료 여행</div><div class="big">{total}</div></div><div class="stat-card"><div class="muted">해외 / 국내</div><div class="big">{overseas} / {domestic}</div></div><div class="stat-card"><div class="muted">누적 여행일</div><div class="big">{days}일</div></div><div class="stat-card"><div class="muted">방문 국가</div><div class="big">{len(country)}개</div></div></div>'

    def bars(title,data,limit=12):
        items=data.most_common(limit); mx=max([v for _,v in items],default=1); s=f'<div class="section-title"><h2>{base.H(title)}</h2></div><div class="home-card"><div class="bar-list">'
        for k,v in items:
            s+=f'<div class="bar-row"><div>{base.H(k)}</div><div class="bar-track"><div class="bar-fill" style="width:{max(4,int(v/mx*100))}%"></div></div><b>{v}</b></div>'
        return s+'</div></div>'

    body+=bars('연도별 여행 횟수',years,20)+bars('국가별 방문 횟수',country,15)+bars('가족 구성별 여행',companions,10)
    return base.page('여행 통계',body)


@app.route('/travel-search')
def travel_search():
    q=(base.request.args.get('q') or '').strip(); rows=[]
    if q:
        like='%'+q+'%'; c=base.db()
        rows=c.execute('''
            SELECT t.id,t.start_date,t.end_date,t.title,t.country,t.region,t.lodging,t.transport,t.notes,
                   group_concat(coalesce(i.title,'') || ' ' || coalesce(i.place,'') || ' ' || coalesce(i.detail,''),' | ') itinerary_text
            FROM trips t LEFT JOIN itinerary i ON i.trip_id=t.id
            WHERE t.title LIKE ? OR t.country LIKE ? OR t.region LIKE ? OR t.lodging LIKE ? OR t.transport LIKE ? OR t.notes LIKE ?
               OR i.title LIKE ? OR i.place LIKE ? OR i.detail LIKE ?
            GROUP BY t.id ORDER BY t.start_date DESC
        ''',(like,like,like,like,like,like,like,like,like)).fetchall(); c.close()
    form=f'<form class="search-form" method="get"><input name="q" value="{base.H(q)}" placeholder="나라 · 도시 · 숙소 · 항공편 · 일정 · 메모 검색"><button class="btn">검색</button></form>'
    body=form
    if q:
        body+=f'<div class="muted" style="margin-bottom:10px">“{base.H(q)}” 검색 결과 {len(rows)}건</div>'
        if not rows: body+='<div class="home-card muted">검색 결과가 없습니다.</div>'
        for r in rows:
            snippets=[]
            for label,key in [('숙소','lodging'),('교통','transport'),('메모','notes')]:
                val=r[key] or ''
                if q.lower() in val.lower(): snippets.append(f'{label}: {val}')
            it=r['itinerary_text'] or ''
            if q.lower() in it.lower(): snippets.append('세부 일정: '+it[:220])
            body+=f'<div class="search-result"><h3><a class="home-link" href="/trip/{r["id"]}">{base.H(r["title"])}</a></h3><div class="search-meta">{base.H(r["start_date"])} ~ {base.H(r["end_date"])} · {base.H(r["country"])} · {base.H(r["region"])}</div>'
            for s in snippets[:3]: body+=f'<div style="margin-top:6px">{base.H(s)}</div>'
            body+='</div>'
    else:
        body+='<div class="home-card"><b>한 번에 찾기</b><div class="muted" style="margin-top:5px">여행명, 국가, 도시, 숙소, 항공·교통, 세부 일정, 장소, 메모를 모두 검색합니다.</div></div>'
    return base.page('통합 검색',body)
