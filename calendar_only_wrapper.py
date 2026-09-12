from datetime import date, datetime, timedelta
import calendar as pycal
import riley_recurring_wrapper as recurring
import family_ui_wrapper as family_ui
import app as base

app = recurring.app


def _family_events_without_riley_academy(start, end):
    """Family calendar keeps Riley's one-off events, but hides recurring Riley academy events."""
    events = list(base.event_rows(start, end))
    recurring_riley = recurring._recurring_timed_google(start, end, '지유')
    recurring_keys = {
        (x['date'].isoformat(), (x.get('title') or '').strip())
        for x in recurring_riley
    }

    out = []
    for e in events:
        d = dict(e)
        is_riley_google = d.get('source') == 'google' and (d.get('person') or '').strip() == '지유'
        key = (str(d.get('start_date') or '')[:10], (d.get('title') or '').strip())
        if is_riley_google and key in recurring_keys:
            continue
        out.append(e)
    return out


def family_calendar_only():
    view=(base.request.args.get('view') or 'month').lower()
    q=base.qdate(base.request.args.get('date','')) or date.today()
    today=date.today()

    if view=='week':
        start=q-timedelta(days=q.weekday())
        end=start+timedelta(days=6)
        prev=(start-timedelta(days=7)).isoformat()
        nxt=(start+timedelta(days=7)).isoformat()
        title=f'{start.strftime("%Y.%m.%d")} ~ {end.strftime("%m.%d")}'
    else:
        start=date(q.year,q.month,1)
        last=pycal.monthrange(q.year,q.month)[1]
        end=date(q.year,q.month,last)
        pm=(start-timedelta(days=1)).replace(day=1)
        nm=(end+timedelta(days=1)).replace(day=1)
        prev=pm.isoformat()
        nxt=nm.isoformat()
        title=f'{q.year}년 {q.month}월'

    events=_family_events_without_riley_academy(start,end)
    tabs=(f'<div class="seg">'
          f'<a class="{"on" if view=="month" else ""}" href="/calendar?view=month&date={q.isoformat()}">월</a>'
          f'<a class="{"on" if view=="week" else ""}" href="/calendar?view=week&date={q.isoformat()}">주</a>'
          f'</div>')
    toolbar=(f'<div class="cal-toolbar">'
             f'<div class="cal-nav">'
             f'<a class="btn s" href="/calendar?view={view}&date={prev}">←</a>'
             f'<a class="btn s" href="/calendar?view={view}&date={today.isoformat()}">오늘</a>'
             f'<a class="btn s" href="/calendar?view={view}&date={nxt}">→</a>'
             f'</div><div class="cal-title">{title}</div>{tabs}</div>')

    if view=='week':
        cal='<div class="week-cards">'
        for i in range(7):
            d=start+timedelta(days=i)
            de=[e for e in events if family_ui._overlaps(e,d)]
            cal+=f'<div class="week-card {"today" if d==today else ""}"><div class="week-date">{d.strftime("%m/%d")}</div><h3>{base.DAYS[i]}</h3>'
            if not de:
                cal+='<div class="muted">일정 없음</div>'
            for e in de:
                dd=dict(e)
                k=family_ui._kind(dd)
                cal+=f'<div class="event-chip {family_ui._kind_class(k)}"><b>{base.H(dd.get("title"))}</b><div class="muted">{base.H(k)}</div></div>'
            cal+='</div>'
        cal+='</div>'
    else:
        cal='<div class="calendar-scroll"><div class="family-month">'+''.join(f'<div class="fm-head">{x}</div>' for x in ['월','화','수','목','금','토','일'])
        grid_start=start-timedelta(days=start.weekday())
        for i in range(42):
            d=grid_start+timedelta(days=i)
            out=d.month!=q.month
            de=[e for e in events if family_ui._overlaps(e,d)]
            num=f'<span class="fm-num {"today" if d==today else ""}">{d.day}</span>'
            cal+=f'<div class="fm-cell {"out" if out else ""}">{num}'
            for e in de[:5]:
                dd=dict(e)
                k=family_ui._kind(dd)
                cal+=f'<div class="fm-event {family_ui._kind_class(k)}" title="{base.H(dd.get("title"))}">{base.H(dd.get("title"))}</div>'
            if len(de)>5:
                cal+=f'<div class="muted">+{len(de)-5}개</div>'
            cal+='</div>'
        cal+='</div></div>'

    return base.page('가족 달력', toolbar+cal)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/calendar':
        app.view_functions[rule.endpoint]=family_calendar_only
