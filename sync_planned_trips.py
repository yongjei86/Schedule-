import os
import sqlite3

DB = os.getenv('DB_PATH', '/data/family_travel.db')
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
MARKER = '[2027계획동기화]'


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


def sync_daily_itinerary(trip_id, rows):
    # Remove old undated sync placeholders. For dated rows, update only rows still carrying
    # the sync marker; once a user edits a card the marker is removed and future deploys
    # leave that date untouched.
    c.execute("delete from itinerary where trip_id=? and (item_date is null or item_date='') and detail like ?", (trip_id, MARKER + '%'))
    for sort_order, item_date, day_label, city, hotel, summary in rows:
        existing = c.execute('select * from itinerary where trip_id=? and item_date=? order by id limit 1', (trip_id, item_date)).fetchone()
        if existing:
            if str(existing['detail'] or '').startswith(MARKER):
                c.execute('''update itinerary set day_label=?,time_text='',title=?,place=?,detail=?,sort_order=? where id=?''',
                          (day_label, city, hotel, MARKER + summary, sort_order, existing['id']))
            continue
        c.execute('''insert into itinerary(trip_id,item_date,day_label,time_text,title,place,detail,sort_order)
                     values(?,?,?,?,?,?,?,?)''',
                  (trip_id,item_date,day_label,'',city,hotel,MARKER + summary,sort_order))


EUROPE = [
    (10,'2027-01-02','1일차','로마','Hotel Artemide','로마 도착·체크인. 도착 시간에 따라 콜로세움·포로 로마노·팔라티노 언덕.'),
    (20,'2027-01-03','2일차','로마','Hotel Artemide','바티칸 박물관·시스티나 성당·성 베드로 대성당.'),
    (30,'2027-01-04','3일차','로마','Hotel Artemide','트레비 분수·판테온·나보나 광장·스페인 계단.'),
    (40,'2027-01-05','4일차','피렌체','c-hotels Club','로마 → 피렌체 이동. 두오모·시뇨리아 광장 중심 일정.'),
    (50,'2027-01-06','5일차','피렌체','c-hotels Club','우피치 미술관 09:00 예정·베키오 다리.'),
    (60,'2027-01-07','6일차','피렌체','c-hotels Club','아카데미아 미술관 10:30 예정·미켈란젤로 광장. 토스카나 일정은 선택안.'),
    (70,'2027-01-08','7일차','베네치아','Hotel Saturnia & International','피렌체 → 베네치아 이동. 산마르코 광장 주변 산책.'),
    (80,'2027-01-09','8일차','베네치아','Hotel Saturnia & International','산마르코 대성당·두칼레 궁전·곤돌라.'),
    (90,'2027-01-10','9일차','베네치아','Hotel Saturnia & International','리알토 다리·베네치아 워킹. 무라노·부라노는 선택안.'),
    (100,'2027-01-11','10일차','바르셀로나','Hotel Jazz','베네치아 → 바르셀로나 이동. 체크인 후 람블라 거리 중심 가벼운 일정.'),
    (110,'2027-01-12','11일차','바르셀로나','Hotel Jazz','사그라다 파밀리아 중심 일정.'),
    (120,'2027-01-13','12일차','바르셀로나','Hotel Jazz','구엘 공원 중심 일정.'),
    (130,'2027-01-14','13일차','바르셀로나','Hotel Jazz','카사 바트요·바르셀로나 자유 일정.'),
    (140,'2027-01-15','14일차','세비야','Hotel Fernando III','바르셀로나 → 세비야 이동. 스페인 광장 중심 일정.'),
    (150,'2027-01-16','15일차','세비야','Hotel Fernando III','레알 알카사르 중심 일정.'),
    (160,'2027-01-17','16일차','세비야','Hotel Fernando III','세비야 대성당·시내 자유 일정.'),
    (170,'2027-01-18','17일차','그라나다','Hotel Saray','세비야 → 그라나다 이동. 체크인 후 가벼운 시내 일정.'),
    (180,'2027-01-19','18일차','그라나다','Hotel Saray','알함브라 궁전 중심 일정.'),
    (190,'2027-01-20','19일차','마드리드','Hotel Regina','그라나다 → 마드리드 이동. 체크인 후 자유 일정.'),
    (200,'2027-01-21','20일차','마드리드','Hotel Regina','프라도 미술관·왕궁은 예정 후보. 세부 일정 조정 가능.'),
    (210,'2027-01-22','21일차','마드리드 → 도쿄','-','마드리드 출발. 16:55 도쿄행 항공편 일정 기준.'),
    (220,'2027-01-23','22일차','귀국 이동','-','귀국 이동일. 도쿄 이후 세부 항공·도착 일정은 확인 후 수정.'),
]

SINGAPORE = [
    (10,'2027-08-07','1일차','싱가포르','미정','싱가포르 도착·체크인. 세부 방문지는 추후 확정.'),
    (20,'2027-08-08','2일차','싱가포르','미정','싱가포르 시내 일정. 주요 방문지는 아직 미정.'),
    (30,'2027-08-09','3일차','Disney Adventure','Disney Adventure','Disney Adventure 승선. 3박 크루즈 시작.'),
    (40,'2027-08-10','4일차','Disney Adventure','Disney Adventure','Sea Day. 선내 프로그램 중심 일정.'),
    (50,'2027-08-11','5일차','Disney Adventure','Disney Adventure','Sea Day. 선내 프로그램 중심 일정.'),
    (60,'2027-08-12','6일차','싱가포르','미정','Disney Adventure 하선 후 싱가포르 이동·체크인.'),
    (70,'2027-08-13','7일차','싱가포르','미정','싱가포르 자유 일정. 주요 방문지는 아직 미정.'),
    (80,'2027-08-14','8일차','싱가포르','미정','싱가포르 자유 일정. 주요 방문지는 아직 미정.'),
    (90,'2027-08-15','9일차','싱가포르 → 귀국','-','귀국일. 세부 항공 일정에 맞춰 최종 수정.'),
]


europe_id = upsert_trip(
    '2027-01-02','2027-01-23',
    '이탈리아·스페인',
    '로마 · 피렌체 · 베네치아 · 바르셀로나 · 세비야 · 그라나다 · 마드리드',
    '이탈리아·스페인 가족여행',
    '가족4','해외','예정',
    lodging='Hotel Artemide · c-hotels Club · Hotel Saturnia & International · Hotel Jazz · Hotel Fernando III · Hotel Saray · Hotel Regina',
    notes='2027 겨울 유럽 가족여행. 날짜별 카드에서 도시·호텔·주요 방문지를 직접 수정 가능. 일부 방문지는 예정안이며 변경 가능.',
    keywords=('이탈리아','스페인','유럽')
)
sync_daily_itinerary(europe_id, EUROPE)

singapore_id = upsert_trip(
    '2027-08-07','2027-08-15',
    '싱가포르',
    '싱가포르 · Disney Adventure',
    '싱가포르·Disney Adventure 가족여행',
    '가족4','해외','검토 중',
    lodging='싱가포르 호텔 미정 · Disney Adventure',
    notes='싱가포르 가족여행 + Disney Adventure 3박 크루즈. 8/9 승선, 8/12 하선. 싱가포르 호텔과 세부 방문지는 확정 후 날짜 카드에서 수정.',
    keywords=('싱가포르','Disney Adventure','디즈니')
)
sync_daily_itinerary(singapore_id, SINGAPORE)

c.commit()
c.close()
print('2027 daily trip plans synced:', europe_id, len(EUROPE), singapore_id, len(SINGAPORE))
