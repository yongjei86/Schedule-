import os, sqlite3
from datetime import datetime
DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
if 'companion' not in cols: c.execute("ALTER TABLE riley_reading ADD COLUMN companion TEXT DEFAULT ''")
books=[
('추피의 할로윈 파티','생활','계절 · 문화'),
('추피의 장난감','생활','생활'),
('추피가 동물원에 놀러 갔어요','지식','동물 · 생활'),
('추피는 잠자기가 싫어요','생활','수면 · 생활습관'),
('추피가 숲에 갔어요','지식','자연 · 숲 체험'),
('추피가 크리스마스 파티를 해요','생활','계절 · 문화'),
]
day='2026-10-05'
for title,genre,summary in books:
    row=c.execute("SELECT id FROM riley_reading WHERE child='혜온' AND title=? AND read_date=? LIMIT 1",(title,day)).fetchone()
    if not row:
        c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,'한국어',genre,'','',day,0,summary,datetime.now().isoformat(timespec='seconds'),'혜온','아빠'))
# same-day rereads: preserve as separate reading events
for title,genre,summary in [('추피는 잠자기가 싫어요','생활','수면 · 생활습관 · 같은 날 재독'),('추피가 숲에 갔어요','지식','자연 · 숲 체험 · 같은 날 재독')]:
    n=c.execute("SELECT COUNT(*) n FROM riley_reading WHERE child='혜온' AND title=? AND read_date=?",(title,day)).fetchone()['n']
    if n<2:
        c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,'한국어',genre,'','',day,0,summary,datetime.now().isoformat(timespec='seconds'),'혜온','아빠'))
c.commit(); c.close()
print('Hyeon 2026-10-05: 6 titles, 8 reading events saved')
