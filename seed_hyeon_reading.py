import os
import sqlite3
from datetime import datetime

DB=os.getenv('DB_PATH','/data/family_travel.db')
BOOKS=[
 ('Rapunzel Can','영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ('Family','영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ("Belle's Wedding Day",'영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ('What Is a Friend?','영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ("Belle's Tea Party",'영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ('Safe!','영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ('In the Castle','영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ("Cinderella's Wedding",'영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
 ('The Snowy Day','영어','영어 원서','2026-09-13','Disney Reading Adventures Level 1'),
]

c=sqlite3.connect(DB)
c.row_factory=sqlite3.Row
try:
 cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
 if not cols:
  print('Hyeon reading seed skipped: riley_reading table not ready')
 else:
  added=0
  for title,language,genre,read_date,summary in BOOKS:
   exists=c.execute('select 1 from riley_reading where child=? and title=? and read_date=? limit 1',('혜온',title,read_date)).fetchone()
   if exists:
    continue
   c.execute('insert into riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child) values(?,?,?,?,?,?,?,?,?,?)',(title,language,genre,'','',read_date,0,summary,datetime.now().isoformat(timespec='seconds'),'혜온'))
   added+=1
  c.commit()
  print(f'Hyeon reading seed added: {added}')
finally:
 c.close()
