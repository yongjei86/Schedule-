import os, sqlite3
from datetime import datetime
DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
if 'companion' not in cols: c.execute("ALTER TABLE riley_reading ADD COLUMN companion TEXT DEFAULT ''")
books=[
 ('Let Me Help You, Too!','Disney English Reading Club Sight Words Book 2'),
 ('I Love Colors!','Scholastic Noodles Level 1 · Hans Wilhelm'),
 ('Ask for Help!','Disney English Reading Club Sight Words Book 1'),
 ('Friends for a Princess','Disney Fun to Read Level K'),
 ('Win the Big Blue Ribbon!','Disney English Reading Club Sight Words Book 3'),
]
for title,summary in books:
 row=c.execute("SELECT id FROM riley_reading WHERE child='혜온' AND title=? AND read_date='2026-09-15' LIMIT 1",(title,)).fetchone()
 if row: c.execute("UPDATE riley_reading SET companion='아빠', summary=? WHERE id=?",(summary,row['id']))
 else: c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,'영어','리더스','','','2026-09-15',0,summary,datetime.now().isoformat(timespec='seconds'),'혜온','아빠'))
c.commit(); c.close()
print('Hyeon Sep15 dad reading saved: 5')