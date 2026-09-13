import os
import sqlite3

DB = os.getenv('DB_PATH', '/data/family_travel.db')
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row


def find_trip(start_date, keywords):
    rows = c.execute("select * from trips where start_date=? order by id", (start_date,)).fetchall()
    for r in rows:
        text = ' '.join(str(r[k] or '') for k in ('country','region','title','notes'))
        if any(k in text for k in keywords):
            return r['id']
    return None


def upsert_trip(start_date, end_date, country, region, title, companions, trip_type, status, lodging='', transport='', notes='', keywords=()):
    trip_id = find_trip(start_date, keywords or (title,))
    if trip_id:
        c.execute('''update trips set end_date=?,country=?,region=?,title=?,companions=?,trip_type=?,status=?,lodging=?,transport=?,notes=? where id=?''',
                  (end_date,country,region,title,companions,trip_type,status,lodging,transport,notes,trip_id))
        return trip_id
    cur = c.execute('''insert into trips(start_date,end_date,country,region,title,companions,trip_type,status,lodging,transport,notes)
                       values(?,?,?,?,?,?,?,?,?,?,?)''',
                    (start_date,end_date,country,region,title,companions,trip_type,status,lodging,transport,notes))
    return cur.lastrowid


def sync_itinerary(trip_id, rows):
    # Only replace itinerary rows created by this sync marker; preserve anything the user entered manually.
    marker = '[2027계획동기화]'
    c.execute("delete from itinerary where trip_id=? and detail like ?", (trip_id, marker + '%'))
    for sort_order, item_date, day_label, time_text, title, place, detail in rows:
        c.execute('''insert into itinerary(trip_id,item_date,day_label,time_text,title,place,detail,sort_order)
                     values(?,?,?,?,?,?,?,?)''',
                  (trip_id,item_date,day_label,time_text,title,place,marker + detail,sort_order))


# 2027 Italy-Spain winter family trip.
# Only dates/details that were already fixed are written. Undecided intermediate city dates stay blank.
europe_id = upsert_trip(
    '2027-01-02','2027-01-23',
    '이탈리아·스페인',
    '로마 · 피렌체 · 바르셀로나 · 그라나다 · 마드리드',
    '이탈리아·스페인 가족여행',
    '가족4','해외','예정',
    notes='겨울 유럽 가족여행. 로마 1/2~1/7 5박. 이후 피렌체 → 바르셀로나 → 그라나다 → 마드리드 순서. 중간 이동일과 세부 일정은 확정되는 대로 추가.',
    keywords=('이탈리아','스페인','유럽')
)
sync_itinerary(europe_id, [
    (10,'2027-01-02','1일차','','로마 도착','로마',' 로마 도착 및 체크인.'),
    (20,'','로마 1/2~1/7','','로마 체류','로마',' 로마 5박 일정.'),
    (30,'','다음 도시','','피렌체','피렌체',' 로마 이후 피렌체 이동.'),
    (40,'','다음 도시','','바르셀로나','바르셀로나',' 피렌체 이후 바르셀로나 이동.'),
    (50,'','다음 도시','','그라나다','그라나다',' 바르셀로나 이후 그라나다 이동.'),
    (60,'','마지막 도시','','마드리드','마드리드',' 그라나다 이후 마드리드 일정 및 귀국.'),
])

# 2027 Singapore + Disney Adventure family trip.
singapore_id = upsert_trip(
    '2027-08-07','2027-08-15',
    '싱가포르',
    '싱가포르 · Disney Adventure',
    '싱가포르·Disney Adventure 가족여행',
    '가족4','해외','검토 중',
    notes='싱가포르 가족여행 + Disney Adventure 3박 크루즈. 크루즈 8/9 승선, 8/12 하선. 항구 기항 없는 Sea Day 중심 일정.',
    keywords=('싱가포르','Disney Adventure','디즈니')
)
sync_itinerary(singapore_id, [
    (10,'2027-08-07','1일차','','싱가포르 도착','싱가포르',' 싱가포르 도착.'),
    (20,'2027-08-09','3일차','','Disney Adventure 승선','싱가포르',' 3박 크루즈 승선.'),
    (30,'2027-08-10','4일차','','Sea Day','Disney Adventure',' 크루즈 해상 일정.'),
    (40,'2027-08-11','5일차','','Sea Day','Disney Adventure',' 크루즈 해상 일정.'),
    (50,'2027-08-12','6일차','','Disney Adventure 하선','싱가포르',' 크루즈 하선 후 싱가포르 일정.'),
    (60,'2027-08-15','9일차','','귀국','싱가포르',' 싱가포르 여행 종료 및 귀국.'),
])

c.commit()
c.close()
print('2027 planned trip data synced:', europe_id, singapore_id)
