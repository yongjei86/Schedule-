import os
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar
import recurring_ical_events

import app as legacy

KST = ZoneInfo('Asia/Seoul')

CALENDARS = [
    ('YJ', 'GCAL_YJ_ICS'),
    ('지유', 'GCAL_RILEY_ICS'),
    ('보미', 'GCAL_BOMI_ICS'),
    ('혜온', 'GCAL_HYEON_ICS'),
    ('가족', 'GCAL_FAMILY_ICS'),
]

_cache = {'at': None, 'items': {}}
CACHE_SECONDS = 300


def _to_date(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=KST)
        return value.astimezone(KST).date()
    if isinstance(value, date):
        return value
    return None


def _fetch_calendar(label, env_name):
    url = os.getenv(env_name, '').strip()
    if not url:
        return []
    r = requests.get(url, timeout=12, headers={'User-Agent': 'YJ-Family-Calendar/1.0'})
    r.raise_for_status()
    cal = Calendar.from_ical(r.content)
    # Expand recurring events over a broad rolling window; view-level filtering happens later.
    start = datetime.now(KST) - timedelta(days=400)
    end = datetime.now(KST) + timedelta(days=1200)
    events = recurring_ical_events.of(cal).between(start, end)
    out = []
    for ev in events:
        try:
            summary = str(ev.get('SUMMARY', '')).strip() or '(제목 없음)'
            ds = _to_date(ev.decoded('DTSTART'))
            de_raw = ev.decoded('DTEND') if ev.get('DTEND') else ev.decoded('DTSTART')
            de = _to_date(de_raw)
            if not ds or not de:
                continue
            # Google all-day DTEND is exclusive; timed events should stay on their actual ending date.
            dtstart = ev.decoded('DTSTART')
            dtend = ev.decoded('DTEND') if ev.get('DTEND') else None
            if isinstance(dtstart, date) and not isinstance(dtstart, datetime) and isinstance(dtend, date) and not isinstance(dtend, datetime):
                de = max(ds, de - timedelta(days=1))
            desc = str(ev.get('DESCRIPTION', '')).replace('\\n', ' ').strip()
            loc = str(ev.get('LOCATION', '')).replace('\\n', ' ').strip()
            uid = str(ev.get('UID', ''))
            out.append({
                'id': 'gcal-' + uid,
                'start_date': ds.isoformat(),
                'end_date': de.isoformat(),
                'title': summary,
                'category': 'Google Calendar',
                'person': label,
                'notes': ' · '.join(x for x in [loc, desc] if x),
                'source': 'google',
            })
        except Exception:
            continue
    return out


def _google_items():
    now = datetime.now(KST)
    if _cache['at'] and (now - _cache['at']).total_seconds() < CACHE_SECONDS:
        return _cache['items']
    items = {}
    for label, env_name in CALENDARS:
        try:
            items[label] = _fetch_calendar(label, env_name)
        except Exception as e:
            print(f'Google Calendar sync failed for {label}: {e}', flush=True)
            items[label] = []
    _cache['at'] = now
    _cache['items'] = items
    return items


def merged_event_rows(start, end):
    # Local web-entered events remain editable and persistent.
    local = []
    c = legacy.db()
    rows = c.execute(
        'select * from calendar_events where start_date<=? and end_date>=? order by start_date,id',
        (end.isoformat(), start.isoformat())
    ).fetchall()
    c.close()
    for r in rows:
        d = dict(r)
        d['source'] = 'local'
        local.append(d)

    google = []
    for label, items in _google_items().items():
        for e in items:
            s = legacy.qdate(e['start_date'])
            en = legacy.qdate(e['end_date'])
            if s and en and s <= end and en >= start:
                google.append(e)
    return sorted(local + google, key=lambda x: (x['start_date'], x['title']))


def merged_event_modals(es):
    b = ''
    for e in es:
        a = ''
        source = e.get('source', 'local') if isinstance(e, dict) else 'local'
        if legacy.admin() and source == 'local':
            dat = ' '.join('data-' + k + '=\"' + legacy.H(e[k]) + '\"' for k in ['id','start_date','end_date','title','category','person','notes'])
            a = f'<div><button class="btn s" {dat} onclick="ee(this)">수정</button><form method="post" action="/event/{e["id"]}/delete" style="display:inline"><button class="btn d">삭제</button></form></div>'
        badge = '구글' if source == 'google' else legacy.H(e['category'])
        b += f'<div class="event"><div><b>{legacy.H(e["start_date"])} ~ {legacy.H(e["end_date"])}</b> · {legacy.H(e["title"])} <span class="pill">{badge}</span><br>{legacy.H(e["person"])} · {legacy.H(e["notes"])}</div>{a}</div>'
    if legacy.admin():
        b += '''<div class="modal" id="em"><div class="card"><div class="head"><h2>가족 일정</h2><button class="btn s" onclick="x('em')">닫기</button></div><form class="form" id="ef" method="post"><label>시작일<input type="date" name="start_date" required></label><label>종료일<input type="date" name="end_date" required></label><label class="full">일정명<input name="title" required></label><label>분류<input name="category"></label><label>사람<input name="person"></label><label class="full">메모<textarea name="notes"></textarea></label><div class="full"><button class="btn">저장</button></div></form></div></div>'''
    return b

legacy.event_rows = merged_event_rows
legacy.event_modals = merged_event_modals
app = legacy.app
