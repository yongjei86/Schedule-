import time
import threading
from datetime import date, timedelta, datetime

import experience_app as exp
import app as base

app = exp.app

base.CSS += '''
/* home cleanup: keep only the global header navigation */
.home-family-list{display:grid;gap:0}.home-family-row{display:grid;grid-template-columns:10px minmax(0,1fr) auto;gap:10px;align-items:center;padding:11px 0;border-bottom:1px solid #edf1f5}.home-family-row:last-child{border-bottom:0}.event-dot{width:8px;height:34px;border-radius:999px;background:#94a3b8}.event-dot.yj{background:#4f7cff}.event-dot.bomi{background:#f08aa8}.event-dot.riley{background:#8b72d6}.event-dot.hyeon{background:#46a67a}.event-dot.holiday{background:#e7a23b}.event-dot.family{background:#6f879f}.event-main{min-width:0}.event-title{font-weight:700;color:#14263f}.event-meta{font-size:12px;color:#718096;margin-top:2px}.event-dday{font-size:12px;font-weight:800;border-radius:999px;padding:4px 8px;background:#f2f5f8;color:#51657b;white-space:nowrap}.event-dday.today{background:#fff0f0;color:#d34646}.family-next h2{margin-bottom:5px}
@media(max-width:700px){.home-family-row{grid-template-columns:8px minmax(0,1fr) auto;gap:8px}.event-dot{width:6px;height:30px}.event-title{font-size:14px}.event-meta{font-size:11px}.event-dday{font-size:11px;padding:3px 7px}}
'''

HOME_CACHE_DAYS = 180
CAL_CACHE_PAST_DAYS = 365
CAL_CACHE_FUTURE_DAYS = 730
HOME_CACHE_REFRESH_SECONDS = 600
_HOME_SYNC_LOCK = threading.Lock()
_LIVE_FAMILY_EVENTS = exp.main.family_events


def _init_home_cache_schema():
    c=base.db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS home_event_cache(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      title TEXT NOT NULL,
      category TEXT,
      person TEXT,
      notes TEXT,
      source TEXT NOT NULL DEFAULT 'google',
      synced_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_home_event_cache_dates ON home_event_cache(start_date,end_date);
    CREATE TABLE IF NOT EXISTS home_cache_meta(
      cache_key TEXT PRIMARY KEY,
      cache_value TEXT NOT NULL
    );
    ''')
    c.commit(); c.close()


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


def _refresh_google_cache():
    if not _HOME_SYNC_LOCK.acquire(blocking=False):
        return
    try:
        today=date.today()
        start=today-timedelta(days=CAL_CACHE_PAST_DAYS)
        end=today+timedelta(days=CAL_CACHE_FUTURE_DAYS)
        events=_LIVE_FAMILY_EVENTS(start,end)
        google_rows=[]
        for raw in events:
            e=dict(raw)
            if e.get('source')!='google':
                continue
            sd=str(e.get('start_date') or '')[:10]
            ed=str(e.get('end_date') or sd)[:10] or sd
            if not sd:
                continue
            google_rows.append((sd,ed,str(e.get('title') or ''),str(e.get('category') or ''),str(e.get('person') or ''),str(e.get('notes') or ''),'google'))

        # Keep the last good snapshot if Google is temporarily unavailable.
        has_sources=bool(exp.main.gcal._sources())
        if has_sources and not google_rows:
            return

        now=datetime.now().isoformat(timespec='seconds')
        c=base.db()
        c.execute('delete from home_event_cache')
        if google_rows:
            c.executemany('insert into home_event_cache(start_date,end_date,title,category,person,notes,source,synced_at) values(?,?,?,?,?,?,?,?)',[r+(now,) for r in google_rows])
        c.execute("insert or replace into home_cache_meta(cache_key,cache_value) values('google_last_sync',?)",(now,))
        c.commit(); c.close()
    except Exception as e:
        print(f'Google event DB cache refresh failed: {type(e).__name__}', flush=True)
    finally:
        _HOME_SYNC_LOCK.release()


def _home_cache_loop():
    time.sleep(2)
    while True:
        _refresh_google_cache()
        time.sleep(HOME_CACHE_REFRESH_SECONDS)


def _cached_calendar_events(start, end):
    """DB-only event source for the family calendar: local + cached Google + trips."""
    c=base.db()
    local=[dict(x) for x in c.execute(
        'select * from calendar_events where start_date<=? and end_date>=? order by start_date,id',
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    cached=[dict(x) for x in c.execute(
        'select start_date,end_date,title,category,person,notes,source from home_event_cache where start_date<=? and end_date>=? order by start_date,id',
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    trips=[dict(x) for x in c.execute(
        "select id,start_date,end_date,title,region,companions from trips where start_date<=? and end_date>=? order by start_date,id",
        (end.isoformat(),start.isoformat())
    ).fetchall()]
    c.close()

    out=[]
    for e in local:
        e['source']='local'
        out.append(e)
    out.extend(cached)
    for r in trips:
        out.append({
            'id':f'trip:{r["id"]}',
            'start_date':r.get('start_date') or '',
            'end_date':r.get('end_date') or r.get('start_date') or '',
            'title':r.get('title') or '',
            'category':'여행',
            'person':r.get('companions') or '',
            'notes':r.get('region') or '',
            'source':'trip',
            'trip_id':r.get('id'),
        })
    out.sort(key=lambda x:(str(x.get('start_date') or ''),str(x.get('title') or '')))
    return out


def _cached_family_events(today, days=HOME_CACHE_DAYS):
    return _cached_calendar_events(today,today+timedelta(days=days))


def _upcoming_events(today, days=180, limit=10):
    events=_cached_family_events(today,days)
    out=[]
    seen=set()
    for e in events:
        if e.get('source')=='trip' or (e.get('category') or '')=='여행':
            continue
        compact=(e.get('title') or '').replace(' ','')
        if '청소아줌마' in compact:
            continue
        sd=exp._safe_date(str(e.get('start_date') or '')[:10])
        ed=exp._safe_date(str(e.get('end_date') or e.get('start_date') or '')[:10])
        if not sd or (ed and ed<today):
            continue
        key=(sd.isoformat(),str(e.get('end_date') or ''),str(e.get('title') or ''),str(e.get('person') or ''))
        if key in seen:
            continue
        seen.add(key)
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

    body='<div class="next-trip-grid">'+exp._trip_card(domestic,today,'다음 국내 여행')+exp._trip_card(overseas,today,'다음 해외 여행')+'</div>'
    body+='<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-family-list">'
    if not family_events:
        body+='<div class="muted" style="padding:10px 0">등록된 가족 일정이 없습니다.</div>'
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


_init_home_cache_schema()
threading.Thread(target=_home_cache_loop,daemon=True,name='google-event-db-cache').start()

# Make the family calendar DB-only as well. The original live reader is kept only
# for the background refresh above, so page requests no longer wait for Google.
exp.main.family_events=_cached_calendar_events

for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/':
        app.view_functions[rule.endpoint]=clean_family_home


@app.before_request
def force_clean_home():
    if base.request.method=='GET' and base.request.path=='/':
        return clean_family_home()
    return None


@app.after_request
def prevent_stale_home_cache(response):
    if base.request.path=='/':
        response.headers['Cache-Control']='no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma']='no-cache'
        response.headers['Expires']='0'
    return response
