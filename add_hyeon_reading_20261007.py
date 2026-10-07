import os, sqlite3
from datetime import datetime
DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
if 'companion' not in cols: c.execute("ALTER TABLE riley_reading ADD COLUMN companion TEXT DEFAULT ''")
books=[
('왜 고집 부리면 안 돼?','지식','생활습관 · 사회성'),
('왜 늦게 자면 안 돼?','지식','생활습관 · 수면'),
('왜 예방 주사를 맞아야 돼?','지식','건강 · 예방접종'),
('왜 약속을 안 지키면 안 돼?','지식','사회성 · 약속'),
('왜 커피 마시면 안 돼?','지식','건강 · 식생활'),
('왜 약 안 먹으면 안 돼?','지식','건강 · 약'),
('피터 팬','창작','디즈니 골든 명작'),
]
day='2026-10-07'
for title,genre,summary in books:
 row=c.execute("SELECT id FROM riley_reading WHERE child='혜온' AND title=? AND read_date=? LIMIT 1",(title,day)).fetchone()
 if not row:
  c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,'한국어',genre,'','',day,0,summary,datetime.now().isoformat(timespec='seconds'),'혜온','아빠'))
 else:
  c.execute("UPDATE riley_reading SET companion='아빠' WHERE id=?",(row['id'],))
c.commit(); c.close()
print('Hyeon 2026-10-07: 7 books saved, companion dad')
