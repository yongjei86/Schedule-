from flask import redirect

import home_tasks_only_app as base

app = base.app
MARKER = '[2027계획동기화]'
TARGET_STARTS = {'2027-01-02', '2027-08-07'}

base.CSS += '''
.trip-day-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
.trip-day-card{width:100%;text-align:left;background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:13px;cursor:pointer;color:#14263f;font:inherit;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease}
.trip-day-card:hover{transform:translateY(-1px);box-shadow:0 5px 16px #10203012;border-color:#b9c9d9}
.trip-day-top{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:9px}.trip-day-date{font-weight:800}.trip-day-label{font-size:11px;color:#718096;background:#eef3f8;border-radius:999px;padding:4px 7px;white-space:nowrap}
.trip-day-city{font-size:17px;font-weight:800;margin-bottom:6px}.trip-day-hotel{font-size:12px;color:#596b80;margin-bottom:7px}.trip-day-summary{font-size:13px;color:#44566d;line-height:1.45}.trip-day-edit-hint{font-size:11px;color:#8a98a9;margin-top:9px}
.trip-overview{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-bottom:14px}.trip-overview .dashcard{margin:0}.trip-actions{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 12px}
@media(max-width:760px){.trip-day-grid{grid-template-columns:1fr}.trip-overview{grid-template-columns:1fr 1fr}}
@media(max-width:440px){.trip-overview{grid-template-columns:1fr}}
'''

base.JS += '''
function editTripDay(el){
 const d=el.dataset;
 const f=document.getElementById('tdf');
 f.action='/trip-day/'+d.id+'/edit';
 document.getElementById('td-date').value=d.date||'';
 document.getElementById('td-day-label').value=d.day_label||'';
 document.getElementById('td-city').value=d.city||'';
 document.getElementById('td-hotel').value=d.hotel||'';
 document.getElementById('td-summary').value=d.summary||'';
 o('tdm');
}
'''


def clean_detail(value):
    s = str(value or '')
    return s[len(MARKER):].strip() if s.startswith(MARKER) else s.strip()


def target_trip(row):
    return bool(row and (row['start_date'] in TARGET_STARTS or ('2027' in str(row['start_date'] or '') and any(k in str(row['title'] or '') for k in ('이탈리아', '싱가포르')))))


def day_attrs(row):
    return ('data-id="%s" data-date="%s" data-day_label="%s" data-city="%s" data-hotel="%s" data-summary="%s"' % (
        base.H(row['id']), base.H(row['item_date']), base.H(row['day_label']), base.H(row['title']), base.H(row['place']), base.H(clean_detail(row['detail']))
    ))


previous_trip_view = None
for rule in list(app.url_map.iter_rules()):
    if rule.rule == '/trip/<int:trip_id>':
        previous_trip_view = app.view_functions[rule.endpoint]
        break


def trip_day_detail(trip_id):
    c = base.db()
    trip = c.execute('select * from trips where id=?', (trip_id,)).fetchone()
    days = c.execute("select * from itinerary where trip_id=? and item_date is not null and item_date<>'' order by item_date,sort_order,id", (trip_id,)).fetchall()
    c.close()
    if not trip:
        return base.abort(404)
    if not target_trip(trip):
        return previous_trip_view(trip_id)

    back = '/past' if trip['status'] == '완료' else '/future'
    actions = (f'<div class="trip-actions"><a class="btn s" href="{back}">← 여행 목록</a>'
               f'<a class="btn" href="/trip/{trip_id}/plan">여행 준비</a></div>')
    overview = (f'<div class="trip-overview">'
                f'<div class="dashcard"><span class="muted">여행 일자</span><h3>{base.H(trip["start_date"])} ~ {base.H(trip["end_date"])}</h3></div>'
                f'<div class="dashcard"><span class="muted">지역</span><h3>{base.H(trip["region"])}</h3></div>'
                f'<div class="dashcard"><span class="muted">함께</span><h3>{base.H(trip["companions"])}</h3></div>'
                f'</div>')

    body = actions + overview + '<h2 class="sectiontitle">날짜별 일정</h2><div class="muted">날짜 카드를 누르면 도시·호텔·주요 방문지를 바로 수정할 수 있습니다.</div><div class="trip-day-grid">'
    if not days:
        body += '<div class="dashcard muted">날짜별 일정이 없습니다.</div>'
    for r in days:
        summary = clean_detail(r['detail'])
        hotel = r['place'] or '-'
        body += (f'<button type="button" class="trip-day-card" {day_attrs(r)} onclick="editTripDay(this)">'
                 f'<div class="trip-day-top"><span class="trip-day-date">{base.H(r["item_date"])}</span><span class="trip-day-label">{base.H(r["day_label"] or "")}</span></div>'
                 f'<div class="trip-day-city">{base.H(r["title"] or "미정")}</div>'
                 f'<div class="trip-day-hotel">호텔 · {base.H(hotel)}</div>'
                 f'<div class="trip-day-summary">{base.H(summary) or "세부 일정 미정"}</div>'
                 f'<div class="trip-day-edit-hint">눌러서 수정</div></button>')
    body += '</div>'
    body += f'<h2 class="sectiontitle" style="margin-top:20px">메모</h2><div class="dashcard">{base.H(trip["notes"]) or "-"}</div>'
    body += '''
<div class="modal" id="tdm"><div class="card"><div class="head"><h2>날짜 일정 수정</h2><button class="btn s" type="button" onclick="x('tdm')">닫기</button></div>
<form id="tdf" method="post" class="form">
<label>날짜<input id="td-date" type="date" name="item_date" required></label>
<label>일차<input id="td-day-label" name="day_label" placeholder="예: 3일차"></label>
<label>도시<input id="td-city" name="title" required placeholder="예: 로마"></label>
<label>호텔<input id="td-hotel" name="place" placeholder="예: Hotel Artemide"></label>
<label class="full">간략 내용 · 주요 방문지<textarea id="td-summary" name="detail" placeholder="예: 바티칸 박물관 · 시스티나 성당"></textarea></label>
<div class="full" style="display:flex;justify-content:flex-end;gap:7px"><button class="btn s" type="button" onclick="x('tdm')">취소</button><button class="btn" type="submit">저장</button></div>
</form></div></div>'''
    return base.page(trip['title'], body)


if previous_trip_view:
    for rule in list(app.url_map.iter_rules()):
        if rule.rule == '/trip/<int:trip_id>':
            app.view_functions[rule.endpoint] = trip_day_detail


@app.route('/trip-day/<int:item_id>/edit', methods=['POST'])
def trip_day_edit(item_id):
    c = base.db()
    row = c.execute('select * from itinerary where id=?', (item_id,)).fetchone()
    if not row:
        c.close(); return base.abort(404)
    f = base.request.form
    item_date = (f.get('item_date') or row['item_date'] or '').strip()
    day_label = (f.get('day_label') or '').strip()
    title = (f.get('title') or '').strip()
    place = (f.get('place') or '').strip()
    detail = (f.get('detail') or '').strip()
    c.execute('update itinerary set item_date=?,day_label=?,title=?,place=?,detail=? where id=?',
              (item_date, day_label, title, place, detail, item_id))
    trip_id = row['trip_id']
    c.commit(); c.close()
    return redirect(f'/trip/{trip_id}')
