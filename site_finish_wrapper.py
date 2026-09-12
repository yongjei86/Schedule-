import calendar_only_wrapper as calendar_only
import app as base

app = calendar_only.app

# Final top navigation: keep only the four primary family workflows.
def final_nav():
    return ('<header><nav><b><a href="/" style="color:#14263f;text-decoration:none">✈️ 우리 가족 기록</a></b>'
            '<div class="nav">'
            '<a href="/past">과거 여행</a>'
            '<a href="/future">향후 여행</a>'
            '<a href="/calendar">가족 달력</a>'
            '<a href="/riley">지유 주간 일정</a>'
            '</div></nav></header>')

base.nav = final_nav

# Mobile polish for the four primary screens.
base.CSS += '''
.trip-actions{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}.trip-edit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.trip-edit-card{background:#fff;border:1px solid #e4e9f0;border-radius:13px;padding:12px}.trip-edit-card .label{font-size:11px;color:#748196;margin-bottom:4px}.itinerary-row{display:grid;grid-template-columns:120px 1fr auto;gap:10px;align-items:start;background:#fff;border:1px solid #e4e9f0;border-radius:12px;padding:10px;margin:8px 0}.itinerary-actions{display:flex;gap:5px;flex-wrap:wrap}.nav a{font-weight:650}.calendar-scroll{border-radius:14px}.family-month{min-width:700px}
@media(max-width:700px){
 nav{padding:9px 10px;align-items:center}.nav{max-width:74vw;gap:2px}.nav a{font-size:12px;padding:7px 8px}.wrap{padding:12px 10px 40px}.hero{padding:15px;border-radius:14px;margin-bottom:12px}.hero h1{font-size:22px}.toolbar,.cal-toolbar,.riley-toolbar{gap:6px}.btn,.nav a{min-height:34px}.trip-edit-grid{grid-template-columns:1fr 1fr}.itinerary-row{grid-template-columns:95px 1fr}.itinerary-actions{grid-column:1/-1}.box{border-radius:12px;-webkit-overflow-scrolling:touch}.box table{min-width:760px}th,td{padding:8px;font-size:12px}.family-month{min-width:660px}.fm-cell{min-height:88px}.riley-week{grid-template-columns:repeat(7,minmax(138px,1fr))}.rday{min-width:138px;padding:8px}.rlesson{padding:7px}.card{padding:13px;margin:2vh auto}.form{gap:8px}}
@media(max-width:430px){.trip-edit-grid{grid-template-columns:1fr}.nav{max-width:70vw}.family-month{min-width:620px}.box table{min-width:720px}}
'''


def _trip_data_attrs(r):
    keys=['id','start_date','end_date','country','region','title','companions','trip_type','status','lodging','transport','notes']
    return ' '.join('data-'+k+'="'+base.H(r[k])+'"' for k in keys)


def _itinerary_data_attrs(x):
    keys=['id','trip_id','item_date','day_label','time_text','title','place','detail','sort_order']
    return ' '.join('data-'+k+'="'+base.H(x[k])+'"' for k in keys)


def editable_trip_detail(trip_id):
    c=base.db()
    r=c.execute('select * from trips where id=?',(trip_id,)).fetchone()
    its=c.execute('select * from itinerary where trip_id=? order by sort_order,item_date,id',(trip_id,)).fetchall()
    c.close()
    if not r:
        return base.abort(404)

    back='/past' if r['status']=='완료' else '/future'
    actions=(f'<div class="trip-actions"><a class="btn s" href="{back}">← 여행 목록</a>'
             f'<button class="btn" {_trip_data_attrs(r)} onclick="et(this)">여행 정보 수정</button>'
             f'<button class="btn s" onclick="ni({r["id"]})">+ 세부 일정</button></div>')

    cards='<div class="trip-edit-grid">'
    for label,value in [
        ('여행 일자',f'{r["start_date"]} ~ {r["end_date"]}'),
        ('지역',' · '.join(x for x in [r['country'],r['region']] if x)),
        ('함께',r['companions']),
        ('숙소',r['lodging']),
        ('교통/항공',r['transport']),
        ('상태',r['status'])]:
        cards+=f'<div class="trip-edit-card"><div class="label">{base.H(label)}</div><b>{base.H(value) or "-"}</b></div>'
    cards+='</div>'

    itinerary='<div class="toolbar"><h2 style="margin:0">일자별 일정</h2><button class="btn s" onclick="ni('+str(r['id'])+')">+ 일정 추가</button></div>'
    if not its:
        itinerary+='<div class="trip-edit-card muted">아직 세부 일정이 없습니다.</div>'
    for x in its:
        left=' · '.join(v for v in [x['item_date'],x['day_label'],x['time_text']] if v) or '-'
        itinerary+=(f'<div class="itinerary-row"><div><b>{base.H(left)}</b></div>'
                    f'<div><b>{base.H(x["title"])}</b>'
                    +(f'<br>{base.H(x["place"])}' if x['place'] else '')
                    +(f'<br><span class="muted">{base.H(x["detail"])}</span>' if x['detail'] else '')
                    +'</div>'
                    f'<div class="itinerary-actions"><button class="btn s" {_itinerary_data_attrs(x)} onclick="ei(this)">수정</button>'
                    f'<form method="post" action="/itinerary/{x["id"]}/delete" style="display:inline" onsubmit="return confirm(\'삭제할까요?\')"><button class="btn d">삭제</button></form></div></div>')

    notes=f'<h2 style="margin-top:20px">메모</h2><div class="trip-edit-card">{base.H(r["notes"]) or "-"}</div>'
    if r['start_date']=='2026-08-08' and '발리' in (r['title'] or ''):
        notes+='<div style="margin-top:10px"><a class="btn" href="/photos/bali-2026">📷 발리 사진</a></div>'

    return base.page(r['title'],actions+cards+itinerary+notes+base.mods())


for rule in list(app.url_map.iter_rules()):
    if rule.rule=='/trip/<int:trip_id>':
        app.view_functions[rule.endpoint]=editable_trip_detail
