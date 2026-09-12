from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar
import recurring_ical_events

import family_ui_wrapper as family_ui
import enhancements_wrapper as enhancements
import gcal_wrapper as gcal

app = family_ui.app
KST = ZoneInfo('Asia/Seoul')


def _recurring_timed_google(start, end, name='지유'):
    """Return only recurring timed Google Calendar events for the requested source."""
    out = []
    sources = [s for s in gcal._sources() if s.get('name') == name]
    window_start = datetime.combine(start, dtime.min, tzinfo=KST)
    window_end = datetime.combine(end + timedelta(days=1), dtime.min, tzinfo=KST)

    for src in sources:
        try:
            r = requests.get(src['url'], timeout=10, headers={'User-Agent': 'YJ-Family-Calendar/1.0'})
            r.raise_for_status()
            cal = Calendar.from_ical(r.content)

            # Google Calendar recurring series have an RRULE on the master VEVENT.
            recurring_uids = set()
            for component in cal.walk('VEVENT'):
                if component.get('RRULE'):
                    uid = str(component.get('UID', '')).strip()
                    if uid:
                        recurring_uids.add(uid)

            if not recurring_uids:
                continue

            for ev in recurring_ical_events.of(cal).between(window_start, window_end):
                if str(ev.get('STATUS', '')).upper() == 'CANCELLED':
                    continue
                uid = str(ev.get('UID', '')).strip()
                if uid not in recurring_uids:
                    continue

                ds = ev.decoded('DTSTART') if ev.get('DTSTART') else None
                de = ev.decoded('DTEND') if ev.get('DTEND') else ds
                if not isinstance(ds, datetime):
                    continue
                if ds.tzinfo:
                    ds = ds.astimezone(KST)
                else:
                    ds = ds.replace(tzinfo=KST)
                if isinstance(de, datetime):
                    if de.tzinfo:
                        de = de.astimezone(KST)
                    else:
                        de = de.replace(tzinfo=KST)

                day = ds.date()
                if not (start <= day <= end):
                    continue

                out.append({
                    'date': day,
                    'start': ds.strftime('%H:%M'),
                    'end': de.strftime('%H:%M') if isinstance(de, datetime) else '',
                    'title': str(ev.get('SUMMARY', '(제목 없음)')),
                    'location': str(ev.get('LOCATION', '') or ''),
                    'notes': str(ev.get('DESCRIPTION', '') or ''),
                    'recurring': True,
                })
        except Exception as e:
            print(f'Riley recurring Google timetable sync failed for {src.get("name")}: {e}', flush=True)

    out.sort(key=lambda x: (x['date'], x['start'], x['title']))
    return out


# family_ui_wrapper calls enhancements._timed_google dynamically, so replacing it here
# keeps the existing UI, local-academy fallback, edit/delete controls and deduplication.
enhancements._timed_google = _recurring_timed_google
