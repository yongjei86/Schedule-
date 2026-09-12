from datetime import date, timedelta, datetime
from collections import Counter

import main_app as main
import app as base

app = main.app

base.CSS += '''
.home-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px}.home-card h2{font-size:16px;margin:0 0 10px}.home-list{display:grid;gap:7px}.home-item{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #edf1f5}.home-item:last-child{border-bottom:0}.home-link{color:#14263f;text-decoration:none}.home-link:hover{text-decoration:underline}.quick-row{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 16px}.next-trip-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:12px}.next-trip-card{background:#fff;border:1px solid #dfe6ee;border-radius:15px;padding:14px;min-height:112px}.next-trip-card .kind{font-size:11px;color:#748196;font-weight:700}.next-trip-card .name{font-size:16px;font-weight:800;margin:7px 0 5px}.dday{display:inline-block;font-size:12px;font-weight:800;color:#0f4c81;background:#edf5fb;border-radius:999px;padding:3px 8px}.family-next{margin-bottom:16px}.filter-box{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:12px;margin-bottom:14px}.filter-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr)) auto auto;gap:8px;align-items:end}.filter-field{display:grid;gap:4px}.filter-field label{font-size:11px;color:#748196;font-weight:700}.filter-field select{width:100%;min-height:38px;border:1px solid #d7dfe8;border-radius:9px;background:#fff;padding:7px 9px;font:inherit}.past-summary{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:9px}.past-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.past-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px}.past-card .date{font-size:12px;color:#748196;margin-bottom:4px}.past-card .meta{font-size:12px;color:#66758a;margin-top:5px}.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.stat-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:13px}.stat-card .big{font-size:24px;font-weight:800;margin-top:4px}.bar-list{display:grid;gap:8px}.bar-row{display:grid;grid-template-columns:130px 1fr 45px;gap:9px;align-items:center}.bar-track{height:9px;background:#edf2f7;border-radius:999px;overflow:hidden}.bar-fill{height:100%;background:#0f4c81;border-radius:999px}.section-title{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:18px 0 9px}.section-title h2{margin:0;font-size:18px}.search-form{display:flex;gap:8px;margin-bottom:14px}.search-form input{flex:1}.search-result{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px;margin-bottom:8px}.search-result h3{margin:0 0 5px;font-size:15px}.search-meta{font-size:12px;color:#728096}
@media(max-width:700px){.next-trip-grid,.past-grid{grid-template-columns:1fr}.filter-form{grid-template-columns:1fr 1fr}.filter-form .filter-field:first-child{grid-column:1/-1}.stat-grid{grid-template-columns:repeat(2,1fr)}.bar-row{grid-template-columns:90px 1fr 36px}.search-form{flex-direction:column}}
@media(max-width:430px){.filter-form{grid-template-columns:1fr}.filter-form .filter-field:first-child{grid-column:auto}}
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


def _dday_label(target, today):
    if not target:
        return '-'
    n=(target-today).days
    return 'D-DAY' if n==0 else f'D-{n}'


def _next_trip_by_type(c, today, trip_type):
    return c.execute("select * from trips where start_date>=? and status!='완료' and trip_type=? order by start_date asc,id asc limit 1",(today.isoformat(),trip_type)).fetchone()


def _is_trip_event(e):
    d=dict(e)
    return d.get('source')=='trip' or (d.get('category') or '')=='여행'


def _upcoming_family_events(today, days=180, limit=8):
    events=main.family_events(today,today+timedelta(days=days))
    out=[]
    for e in events:
        d=dict(e)
        if _is_trip_event(d):
            continue
        sd=_safe_date(str(d.get('start_date') or '')[:10])
        ed=_safe_date(str(d.get('end_date') or d.get('start_date') or '')[:10])
        if not sd or (ed and ed<today):
            continue
        out.append((sd,d))
    out.sort(key=lambda x:(x[0],str(x[1].get('title') or '')))
    return out[:limit]


def _trip_card(r, today, kind):
    if not r:
        return f'<div class="next-trip-card"><div class="kind">{kind}</div><div class="name">예정 없음</div></div>'
    td=_safe_date(r['start_date'])
    region=' · '.join(x for x in [r['country'],r['region']] if x)
    return (f'<div class="next-trip-card"><div class="kind">{kind}</div>'
            f'<div class="name"><a class="home-link" href="/trip/{r["id"]}">{base.H(r["title"])}</a></div>'
            f'<span class="dday">{_dday_label(td,today)}</span>'
            f'<div class="muted" style="margin-top:6px">{base.H(r["start_date"])} ~ {base.H(r["end_date"])}</div>'
            f'<div class="muted">{base.H(region) or "-"}</div></div>')


def family_home():
    today=date.today()
    c=base.db(); domestic=_next_trip_by_type(c,today,'국내'); overseas=_next_trip_by_type(c,today,'해외'); c.close()
    family_events=_upcoming_family_events(today)

    quick='<div class="quick-row"><a class="btn" href="/past">과거 여행</a><a class="btn s" href="/future">향후 여행</a><a class="btn s" href="/travel-search">통합 검색</a><a class="btn s" href="/travel-stats">여행 통계</a><a class="btn s" href="/calendar">가족 달력</a><a class="btn s" href="/riley">지유 주간 일정</a></div>'
    body=quick+'<div class="next-trip-grid">'+_trip_card(domestic,today,'다음 국내 여행')+_trip_card(overseas,today,'다음 해외 여행')+'</div>'
    body+='<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-list">'
    if not family_events:
        body+='<div class="muted">180일 내 등록된 가족 일정이 없습니다.</div>'
    for d,e in family_events:
        end=str(e.get('end_date') or '')[:10]
        date_text=d.isoformat() if not end or end==d.isoformat() else f'{d.isoformat()} ~ {end}'
        body+=f'<div class="home-item"><span>{base.H(e.get("title"))}</span><span class="muted">{base.H(date_text)} · {_dday_label(d,today)}</span></div>'
    body+='</div></section>'
    return base.page('우리 가족 기록',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=family_home
        break


def past_filtered():
    year=(base.request.args.get('year') or '').strip()
    country=(base.request.args.get('country') or '').strip()
    people=(base.request.args.get('people') or '').strip()
    c=base.db(); all_rows=c.execute("select * from trips where status='완료' order by start_date desc,id desc").fetchall(); c.close()

    years=sorted({(r['start_date'] or '')[:4] for r in all_rows if (r['start_date'] or '')[:4]},reverse=True)
    countries=sorted({(r['country'] or '').strip() for r in all_rows if (r['country'] or '').strip()})
    peoples=sorted({(r['companions'] or '').strip() for r in all_rows if (r['companions'] or '').strip()})

    rows=[]
    for r in all_rows:
        if year and (r['start_date'] or '')[:4]!=year: continue
        if country and (r['country'] or '').strip()!=country: continue
        if people and (r['companions'] or '').strip()!=people: continue
        rows.append(r)

    def options(values,current,all_label):
        s=f'<option value="">{all_label}</option>'
        for v in values:
            s+=f'<option value="{base.H(v)}" {"selected" if current==v else ""}>{base.H(v)}</option>'
        return s

    body='<div class="filter-box"><form class="filter-form" method="get">'
    body+=f'<div class="filter-field"><label>연도별</label><select name="year">{options(years,year,"전체 연도")}</select></div>'
    body+=f'<div class="filter-field"><label>국가별</label><select name="country">{options(countries,country,"전체 국가")}</select></div>'
    body+=f'<div class="filter-field"><label>인원별</label><select name="people">{options(peoples,people,"전체 인원")}</select></div>'
    body+='<button class="btn">필터 적용</button><a class="btn s" href="/past">초기화</a></form></div>'
    body+=f'<div class="past-summary"><b>과거 여행 {len(rows)}건</b><span class="muted">전체 {len(all_rows)}건</span></div><div class="past-grid">'
    if not rows:
        body+='<div class="home-card muted">조건에 맞는 여행이 없습니다.</div>'
    for r in rows:
        region=' · '.join(x for x in [r['country'],r['region']] if x)
        body+=f'<a class="past-card home-link" href="/trip/{r["id"]}"><div class="date">{base.H(r["start_date"])} ~ {base.H(r["end_date"])}</div><b>{base.H(r["title"])}</b><div class="meta">{base.H(region) or "-"}</div><div class="meta">함께: {base.H(r["companions"]) or "-"}</div></a>'
    body+='</div>'
    return base.page('과거 여행',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/past':
        app.view_functions[rule.endpoint]=past_filtered
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


def travel_search_page():
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


_search_overridden=False
for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/travel-search':
        app.view_functions[rule.endpoint]=travel_search_page
        _search_overridden=True
        break
if not _search_overridden:
    app.add_url_rule('/travel-search','travel_search_page',travel_search_page)
