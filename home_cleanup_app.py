from datetime import date, timedelta

import experience_app as exp
import app as base

app = exp.app

base.CSS += '''
/* home cleanup: keep only the global header navigation */
.home-family-list{display:grid;gap:0}.home-family-row{display:grid;grid-template-columns:10px minmax(0,1fr) auto;gap:10px;align-items:center;padding:11px 0;border-bottom:1px solid #edf1f5}.home-family-row:last-child{border-bottom:0}.event-dot{width:8px;height:34px;border-radius:999px;background:#94a3b8}.event-dot.yj{background:#4f7cff}.event-dot.bomi{background:#f08aa8}.event-dot.riley{background:#8b72d6}.event-dot.hyeon{background:#46a67a}.event-dot.holiday{background:#e7a23b}.event-dot.family{background:#6f879f}.event-main{min-width:0}.event-title{font-weight:700;color:#14263f}.event-meta{font-size:12px;color:#718096;margin-top:2px}.event-dday{font-size:12px;font-weight:800;border-radius:999px;padding:4px 8px;background:#f2f5f8;color:#51657b;white-space:nowrap}.event-dday.today{background:#fff0f0;color:#d34646}.family-next h2{margin-bottom:5px}
@media(max-width:700px){.home-family-row{grid-template-columns:8px minmax(0,1fr) auto;gap:8px}.event-dot{width:6px;height:30px}.event-title{font-size:14px}.event-meta{font-size:11px}.event-dday{font-size:11px;padding:3px 7px}}
'''


def _event_kind(e):
    person=(e.get('person') or '').strip()
    title=(e.get('title') or '').strip()
    category=(e.get('category') or '').strip()
    text=f'{person} {title} {category}'
    holiday_words=('추석','설날','공휴일','휴업일','휴일','연휴','대체공휴일')
    if any(w in text for w in holiday_words):
        return 'holiday','휴일'
    if '보미' in text:
        return 'bomi','보미'
    if '지유' in text:
        return 'riley','지유'
    if '혜온' in text:
        return 'hyeon','혜온'
    if '용제' in text or 'YJ' in text.upper():
        return 'yj','용제'
    return 'family','가족'


def _clean_title(title):
    t=(title or '').strip()
    for prefix in ('보미:','보미 :','지유:','지유 :','혜온:','혜온 :','용제:','용제 :'):
        if t.startswith(prefix):
            return t[len(prefix):].strip()
    return t


def _upcoming_events(today, days=180, limit=10):
    events=exp.main.family_events(today,today+timedelta(days=days))
    out=[]
    for raw in events:
        e=dict(raw)
        if exp._is_trip_event(e):
            continue
        title=(e.get('title') or '').replace(' ','')
        if '청소아줌마' in title:
            continue
        sd=exp._safe_date(str(e.get('start_date') or '')[:10])
        ed=exp._safe_date(str(e.get('end_date') or e.get('start_date') or '')[:10])
        if not sd or (ed and ed<today):
            continue
        out.append((sd,e))
    out.sort(key=lambda x:(x[0],str(x[1].get('title') or '')))
    return out[:limit]


def clean_family_home():
    today=date.today()
    c=base.db()
    domestic=exp._next_trip_by_type(c,today,'국내')
    overseas=exp._next_trip_by_type(c,today,'해외')
    c.close()
    family_events=_upcoming_events(today)

    # No secondary quick navigation here; the global header is the only navigator.
    body='<div class="next-trip-grid">'+exp._trip_card(domestic,today,'다음 국내 여행')+exp._trip_card(overseas,today,'다음 해외 여행')+'</div>'
    body+='<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-family-list">'
    if not family_events:
        body+='<div class="muted" style="padding:10px 0">180일 내 등록된 가족 일정이 없습니다.</div>'
    for d,e in family_events:
        kind,label=_event_kind(e)
        end=str(e.get('end_date') or '')[:10]
        date_text=d.isoformat() if not end or end==d.isoformat() else f'{d.isoformat()} ~ {end}'
        dday=exp._dday_label(d,today)
        today_cls=' today' if dday=='D-DAY' else ''
        title=_clean_title(e.get('title'))
        body+=(f'<div class="home-family-row">'
               f'<span class="event-dot {kind}" title="{base.H(label)}"></span>'
               f'<div class="event-main"><div class="event-title">{base.H(title)}</div>'
               f'<div class="event-meta">{base.H(label)} · {base.H(date_text)}</div></div>'
               f'<span class="event-dday{today_cls}">{base.H(dday)}</span></div>')
    body+='</div></section>'
    return base.page('우리 가족 기록',body)


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=clean_family_home
        break
