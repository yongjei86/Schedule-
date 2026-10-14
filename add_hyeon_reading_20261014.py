import os,sqlite3
from datetime import datetime
db=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(db);c.row_factory=sqlite3.Row
if 'companion' not in {x['name'] for x in c.execute('PRAGMA table_info(riley_reading)')}:c.execute("ALTER TABLE riley_reading ADD COLUMN companion TEXT DEFAULT ''")
books=[('What Am I?','영어','지식','모양과 과일 · N. N. Charles · Leo & Diane Dillon'),('빙봉은 외롭지 않아','한국어','창작','디즈니 골든 명작 · 인사이드 아웃'),('달콤한 경주','한국어','창작','디즈니 골든 명작'),('브라더 베어','한국어','창작','디즈니 골든 명작'),('카','한국어','창작','디즈니 골든 명작')]
for title,language,genre,summary in books:
 row=c.execute("SELECT id FROM riley_reading WHERE child='혜온' AND title=? AND read_date='2026-10-14' LIMIT 1",(title,)).fetchone()
 if row:c.execute("UPDATE riley_reading SET companion='아빠' WHERE id=?",(row['id'],))
 else:c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,language,genre,'','','2026-10-14',0,summary,datetime.now().isoformat(timespec='seconds'),'혜온','아빠'))
c.commit();c.close()
print('Hyeon 2026-10-14: 5 reading records saved')
