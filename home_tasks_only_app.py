from datetime import date

import family_next_app as current
import family_features_app as features
import home_cleanup_app as home
import app as base

app = current.app


def _tasks_card():
    tasks = features._task_rows(False, 5)
    body = '<section class="feature-card" style="margin-top:12px"><h2>할 일</h2><div class="feature-list">'
    if not tasks:
        body += '<div class="muted">미완료 할 일 없음</div>'
    for t in tasks:
        body += (f'<div class="feature-row"><div><b>{base.H(t["title"])}</b>'
                 f'<div class="feature-meta">{base.H(features._task_label(t))}</div></div>'
                 f'<form method="post" action="/tasks/{t["id"]}/toggle"><button class="btn s">완료</button></form></div>')
    body += '<div style="margin-top:8px"><a class="btn s" href="/tasks">전체 할 일 보기</a></div></div></section>'
    return body


def tasks_only_home():
    today = date.today()
    c = base.db()
    domestic = home.exp._next_trip_by_type(c, today, '국내')
    overseas = home.exp._next_trip_by_type(c, today, '해외')
    c.close()
    family_events = home._upcoming_events(today)

    body = '<div class="next-trip-grid">' + home.exp._trip_card(domestic, today, '다음 국내 여행') + home.exp._trip_card(overseas, today, '다음 해외 여행') + '</div>'
    body += '<section class="home-card family-next"><h2>다음 가족 일정</h2><div class="home-family-list">'
    if not family_events:
        body += '<div class="muted" style="padding:10px 0">등록된 가족 일정이 없습니다.</div>'
    for d, e in family_events:
        kind, label = home._event_kind(e)
        end = str(e.get('end_date') or '')[:10]
        date_text = d.isoformat() if not end or end == d.isoformat() else f'{d.isoformat()} ~ {end}'
        dday = home.exp._dday_label(d, today)
        today_cls = ' today' if dday == 'D-DAY' else ''
        title = home._clean_title(e.get('title'))
        body += (f'<div class="home-family-row">'
                 f'<span class="event-dot {kind}" title="{base.H(label)}"></span>'
                 f'<div class="event-main"><div class="event-title">{base.H(title)}</div>'
                 f'<div class="event-meta">{base.H(label)} · {base.H(date_text)}</div></div>'
                 f'<span class="event-dday{today_cls}">{base.H(dday)}</span></div>')
    body += '</div></section>'
    body += _tasks_card()
    return base.page('우리 가족 기록', body)


# home_cleanup_app's before_request calls this module-level function dynamically,
# so replacing it removes the added today/weekly schedule panels while keeping tasks.
home.clean_family_home = tasks_only_home

for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/':
        app.view_functions[rule.endpoint] = tasks_only_home
