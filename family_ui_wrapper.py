from datetime import date, datetime, timedelta
import calendar as pycal
import authless_wrapper as authless
import enhancements_wrapper as enhancements
import app as base

app = authless.app

base.CSS += '''
.family-summary{display:grid;grid-template-columns:1.15fr 1.85fr;gap:12px;margin-bottom:14px}.summary-card{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:14px}.summary-card h3{margin:0 0 10px}.summary-row{display:flex;gap:8px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #edf1f5}.summary-row:last-child{border-bottom:0}.dot{width:9px;height:9px;border-radius:50%;margin-top:5px;flex:0 0 9px}.dot-yj{background:#315c9b}.dot-지유{background:#e98755}.dot-보미{background:#9a66ad}.dot-혜온{background:#46a081}.dot-가족{background:#c99a35}.dot-여행{background:#d64f5b}.dot-local{background:#7d8793}.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:#6f7c8f;margin:8px 0 14px}.legend span{display:flex;gap:5px;align-items:center}.legend i{width:8px;height:8px;border-radius:50%;display:inline-block}.cal-toolbar{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}.cal-nav{display:flex;gap:6px;align-items:center}.cal-title{font-size:20px;font-weight:900}.family-month{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));border-left:1px solid #e4e9f0;border-top:1px solid #e4e9f0;background:#fff;border-radius:14px;overflow:hidden}.fm-head{padding:8px;text-align:center;font-size:12px;color:#748196;background:#f8fafc;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0}.fm-cell{min-height:118px;padding:6px;border-right:1px solid #e4e9f0;border-bottom:1px solid #e4e9f0;overflow:hidden}.fm-cell.out{background:#fafbfd;color:#b2bac5}.fm-num{font-size:12px;font-weight:800;margin-bottom:4px}.fm-num.today{display:inline-block;background:#0f4c81;color:white;border-radius:999px;padding:3px 7px}.fm-event{font-size:10px;padding:4px 5px;margin:3px 0;border-radius:6px;background:#edf2f7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-left:3px solid #7d8793}.fm-event.yj{background:#edf3fc;border-left-color:#315c9b}.fm-event.지유{background:#fff2eb;border-left-color:#e98755}.fm-event.보미{background:#f7eff9;border-left-color:#9a66ad}.fm-event.혜온{background:#edf8f4;border-left-color:#46a081}.fm-event.가족{background:#fff7df;border-left-color:#c99a35}.fm-event.여행{background:#fff0f1;border-left-color:#d64f5b}.week-cards{display:grid;grid-template-columns:repeat(7,minmax(145px,1fr));gap:8px;overflow-x:auto;padding-bottom:8px}.week-card{min-width:145px;background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:10px}.week-card.today{border:2px solid #0f4c81}.week-date{font-size:11px;color:#7b8797}.week-card h3{margin:4px 0 9px}.event-chip{border-radius:9px;padding:8px;margin:6px 0;background:#f2f5f8;font-size:12px;border-left:4px solid #7d8793}.event-chip.yj{border-left-color:#315c9b}.event-chip.지유{border-left-color:#e98755}.event-chip.보미{border-left-color:#9a66ad}.event-chip.혜온{border-left-color:#46a081}.event-chip.가족{border-left-color:#c99a35}.event-chip.여행{border-left-color:#d64f5b}.riley-toolbar{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px}.riley-week{display:grid;grid-template-columns:repeat(7,minmax(150px,1fr));gap:8px;overflow-x:auto;padding-bottom:8px;-webkit-overflow-scrolling:touch}.rday{min-width:150px;background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:10px}.rday.today{border:2px solid #e98755}.rdate{font-size:11px;color:#7c8796}.rday h3{margin:4px 0 10px}.rlesson{background:#fff2eb;border-left:4px solid #e98755;border-radius:9px;padding:8px;margin-bottom:7px;font-size:12px}.rlesson.local{background:#f2f5f8;border-left-color:#7d8793}.rlesson b{display:block;margin-bottom:3px}.rmeta{color:#738095;font-size:11px;line-height:1.45}.row-actions{display:flex;gap:5px;margin-top:6px}.needs-check{margin-top:14px;background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:12px}.needs-check h3{margin:0 0 8px}.needs-item{display:flex;justify-content:space-between;gap:8px;padding:8px 0;border-bottom:1px solid #edf1f5}.needs-item:last-child{border-bottom:0}@media(max-width:700px){.family-summary{grid-template-columns:1fr}.fm-cell{min-height:90px;padding:4px}.fm-event{font-size:9px;padding:3px 4px}.family-month{min-width:720px}.calendar-scroll{overflow-x:auto}.week-cards{grid-template-columns:repeat(7,minmax(140px,1fr))}.riley-week{grid-template-columns:repeat(7,minmax(145px,1fr))}}
'''

PEOPLE = ['YJ','지유','보미','혜온','가족']

def _kind(e):
    d=dict(e)
    if d.get('source')=='trip' or d.get('category')=='여행': return '여행'
    p=(d.get('person') or '').strip()
    if p in PEOPLE: return p
    return 'local'

def _kind_class(k):
    return 'yj' if k=='YJ' else k

def _overlaps(e,d):
    try:
        s=datetime.strptime(str(e['start_date'])[:10],'%Y-%m-%d').date(); en=datetime.strptime(str(e['end_date'])[:10],'%Y-%m-%d').date()
        return s<=d<=en
    except: return False

def _event_line(e, show_date=False):
    d=dict(e); k=_kind(d); title=base.H(d.get('title',''))
    if d.get('source')=='trip' and d.get('trip_id'):
        title=f'<a class="triplink" href="/trip/{d["trip_id"]}">{title}</a>'
    prefix=f'<b>{base.H(d.get("start_date"))}</b> · ' if show_date else ''
    note=base.H(d.get('notes',''))
    return f'<div class="summary-row"><span class="dot dot-{_kind_class(k)}"></span><div>{prefix}{title}<div class="muted">{base.H(k)}'+((' · '+note) if note else '')+'</div></div></div>'

def family_calendar():
    view=(base.request.args.get('view') or 'month').lower()
    q=base.qdate(base.request.args.get('date','')) or date.today()
    today=date.today()
    if view=='week':
        start=q-timedelta(days=q.weekday()); end=start+timedelta(days=6)
        prev=(start-timedelta(days=7)).isoformat(); nxt=(start+timedelta(days=7)).isoformat(); title=f'{start.strftime("%Y.%m.%d")} ~ {end.strftime("%m.%d")}'
    else:
        start=date(q.year,q.month,1); last=pycal.monthrange(q.year,q.month)[1]; end=date(q.year,q.month,last)
        pm=(start-timedelta(days=1)).replace(day=1); nm=(end+timedelta(days=1)).replace(day=1); prev=pm.isoformat(); nxt=nm.isoformat(); title=f'{q.year}년 {q.month}월'
    events=list(base.event_rows(start,end))

    # Today + this week summaries always use live merged calendar rows.
    week0=today-timedelta(days=today.weekday()); week1=week0+timedelta(days=6)
    week_events=list(base.event_rows(week0,week1))
    today_events=[e for e in week_events if _overlaps(e,today)]
    summary='<div class="family-summary"><div class="summary-card"><h3>오늘 일정</h3>'
    summary += ''.join(_event_line(e) for e in today_events) if today_events else '<div class="muted">오늘 일정 없음</div>'
    summary += '</div><div class="summary-card"><h3>이번주 일정</h3>'
    summary += ''.join(_event_line(e,True) for e in week_events) if week_events else '<div class="muted">이번주 일정 없음</div>'
    summary += '</div></div>'

    legend='<div class="legend">'+''.join(f'<span><i class="dot-{_kind_class(k)}"></i>{k}</span>' for k in PEOPLE+['여행'])+'</div>'
    tabs=f'<div class="seg"><a class="{"on" if view=="month" else ""}" href="/calendar?view=month&date={q.isoformat()}">월</a><a class="{"on" if view=="week" else ""}" href="/calendar?view=week&date={q.isoformat()}">주</a></div>'
    toolbar=f'<div class="cal-toolbar"><div class="cal-nav"><a class="btn s" href="/calendar?view={view}&date={prev}">←</a><a class="btn s" href="/calendar?view={view}&date={today.isoformat()}">오늘</a><a class="btn s" href="/calendar?view={view}&date={nxt}">→</a></div><div class="cal-title">{title}</div>{tabs}</div>'

    if view=='week':
        cal='<div class="week-cards">'
        for i in range(7):
            d=start+timedelta(days=i); de=[e for e in events if _overlaps(e,d)]
            cal+=f'<div class="week-card {"today" if d==today else ""}"><div class="week-date">{d.strftime("%m/%d")}</div><h3>{base.DAYS[i]}</h3>'
            if not de: cal+='<div class="muted">일정 없음</div>'
            for e in de:
                dd=dict(e); k=_kind(dd); cal+=f'<div class="event-chip {_kind_class(k)}"><b>{base.H(dd.get("title"))}</b><div class="muted">{base.H(k)}</div></div>'
            cal+='</div>'
        cal+='</div>'
    else:
        cal='<div class="calendar-scroll"><div class="family-month">'+''.join(f'<div class="fm-head">{x}</div>' for x in ['월','화','수','목','금','토','일'])
        grid_start=start-timedelta(days=start.weekday())
        for i in range(42):
            d=grid_start+timedelta(days=i); out=d.month!=q.month; de=[e for e in events if _overlaps(e,d)]
            num=f'<span class="fm-num {"today" if d==today else ""}">{d.day}</span>'
            cal+=f'<div class="fm-cell {"out" if out else ""}">{num}'
            for e in de[:4]:
                dd=dict(e); k=_kind(dd); cal+=f'<div class="fm-event {_kind_class(k)}" title="{base.H(dd.get("title"))}">{base.H(dd.get("title"))}</div>'
            if len(de)>4: cal+=f'<div class="muted">+{len(de)-4}개</div>'
            cal+='</div>'
        cal+='</div></div>'

    all_list='<div class="toolbar" style="margin-top:16px"><b>일정 목록 · '+str(len(events))+'건</b><button class="btn" onclick="ne()">+ 일정 추가</button></div>'+base.event_modals(events)
    return base.page('가족 달력', summary+toolbar+legend+cal+all_list)


def academy_modal():
    opts=''.join(f'<option>{d}</option>' for d in base.DAYS)+ '<option>미정</option>'
    return f'''<div class="modal" id="am"><div class="card"><div class="head"><h2>지유 일정 추가/수정</h2><button class="btn s" onclick="x('am')">닫기</button></div><form class="form" id="af" method="post"><label>요일<select name="day_of_week">{opts}</select></label><label>시작 시간<input type="time" name="start_time"></label><label>종료 시간<input type="time" name="end_time"></label><label>학원/일정명<input name="academy" required></label><label>과목<input name="subject"></label><label>장소<input name="location"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''

def riley_week():
    q=base.qdate(base.request.args.get('date','')) or date.today(); today=date.today()
    mon=q-timedelta(days=q.weekday()); sun=mon+timedelta(days=6)
    ge=enhancements._timed_google(mon,sun,'지유')
    by={mon+timedelta(days=i):[] for i in range(7)}
    for x in ge:
        x=dict(x); x['source']='google'; by[x['date']].append(x)
    c=base.db(); local=c.execute('select * from academy where active=1 order by start_time,id').fetchall(); c.close()
    unknown=[]
    for r in local:
        dayname=(r['day_of_week'] or '').strip()
        if dayname not in base.DAYS:
            unknown.append(r); continue
        d=mon+timedelta(days=base.DAYS.index(dayname))
        # Deduplicate local fallback when Google has same title and time, or very similar title at same time.
        st=r['start_time'] or ''
        duplicate=False
        for x in by[d]:
            if x.get('start','')==st and (x.get('title','').strip()==(r['academy'] or '').strip() or (r['academy'] or '') in x.get('title','') or x.get('title','') in (r['academy'] or '')):
                duplicate=True; break
        if not duplicate:
            by[d].append({'date':d,'start':st,'end':r['end_time'] or '','title':r['academy'] or '일정','location':r['location'] or '', 'subject':r['subject'] or '', 'notes':r['notes'] or '', 'source':'local','local_id':r['id'], 'day_of_week':dayname})
    for d in by: by[d].sort(key=lambda x:(x.get('start') or '99:99',x.get('title','')))
    prev=(mon-timedelta(days=7)).isoformat(); nxt=(mon+timedelta(days=7)).isoformat()
    head=f'<div class="riley-toolbar"><div><a class="btn s" href="/riley?date={prev}">← 이전 주</a> <a class="btn s" href="/riley?date={today.isoformat()}">이번 주</a> <a class="btn s" href="/riley?date={nxt}">다음 주 →</a></div><b>{mon.strftime("%Y.%m.%d")} ~ {sun.strftime("%m.%d")}</b></div>'
    body=head+'<div class="riley-week">'
    for i in range(7):
        d=mon+timedelta(days=i); body+=f'<div class="rday {"today" if d==today else ""}"><div class="rdate">{d.strftime("%m/%d")}</div><h3>{base.DAYS[i]}</h3>'
        if not by[d]: body+='<div class="muted">일정 없음</div>'
        for x in by[d]:
            src=x.get('source'); tm=x.get('start') or '시간 미정'; tm += ('–'+x.get('end')) if x.get('end') else ''
            cls='rlesson' if src=='google' else 'rlesson local'
            body+=f'<div class="{cls}"><b>{base.H(x.get("title"))}</b><div>{base.H(tm)}</div>'
            meta=' · '.join(v for v in [x.get('subject',''),x.get('location',''),x.get('notes','')] if v)
            if meta: body+=f'<div class="rmeta">{base.H(meta)}</div>'
            if src=='local':
                rid=x['local_id']; dat=' '.join('data-'+k+'="'+base.H(x.get(k,''))+'"' for k in ['day_of_week','start','end','title','subject','location','notes'])
                # remap to fields expected by existing ea() JS
                dat=f'data-id="{rid}" data-day_of_week="{base.H(x.get("day_of_week"))}" data-start_time="{base.H(x.get("start"))}" data-end_time="{base.H(x.get("end"))}" data-academy="{base.H(x.get("title"))}" data-subject="{base.H(x.get("subject"))}" data-location="{base.H(x.get("location"))}" data-notes="{base.H(x.get("notes"))}"'
                body+=f'<div class="row-actions"><button class="btn s" {dat} onclick="ea(this)">수정</button><form method="post" action="/academy/{rid}/delete" onsubmit="return confirm(\'삭제할까요?\')"><button class="btn d">삭제</button></form></div>'
            body+='</div>'
        body+=f'<button class="btn s" onclick="na(\'{base.DAYS[i]}\')">+ 일정</button></div>'
    body+='</div>'
    if unknown:
        body+='<div class="needs-check"><h3>요일/시간 확인 필요</h3>'
        for r in unknown:
            dat=f'data-id="{r["id"]}" data-day_of_week="{base.H(r["day_of_week"])}" data-start_time="{base.H(r["start_time"])}" data-end_time="{base.H(r["end_time"])}" data-academy="{base.H(r["academy"])}" data-subject="{base.H(r["subject"])}" data-location="{base.H(r["location"])}" data-notes="{base.H(r["notes"])}"'
            body+=f'<div class="needs-item"><div><b>{base.H(r["academy"])}</b><div class="muted">요일 또는 시간이 미정이라 주간표 밖에 표시</div></div><div class="row-actions"><button class="btn s" {dat} onclick="ea(this)">수정</button><form method="post" action="/academy/{r["id"]}/delete"><button class="btn d">삭제</button></form></div></div>'
        body+='</div>'
    body+='<p class="muted" style="margin-top:10px">주황색은 지유 Google Calendar, 회색은 기존 학원 DB 보완 일정입니다. 같은 시간·같은 일정은 중복 표시하지 않습니다.</p>'+academy_modal()
    return base.page('지유 주간 일정',body)

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/calendar': app.view_functions[rule.endpoint]=family_calendar
    elif rule.rule=='/riley': app.view_functions[rule.endpoint]=riley_week
