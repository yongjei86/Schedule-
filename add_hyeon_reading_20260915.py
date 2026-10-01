import os, sqlite3
from datetime import datetime
DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
if 'companion' not in cols:
    c.execute("ALTER TABLE riley_reading ADD COLUMN companion TEXT DEFAULT ''")
books=[
 ('Up','영어','리더스','세이펜 음원을 들으면서 읽음'),
 ('Ride On!','영어','리더스','Scholastic Word Readers · 세이펜 음원을 들으면서 읽음'),
 ('What Do I Need?','영어','리더스','Scholastic First Little Readers Level A · Deborah Schecter · 세이펜 음원을 들으면서 읽음'),
]
for title,language,genre,summary in books:
    row=c.execute("SELECT id FROM riley_reading WHERE child='혜온' AND title=? AND read_date='2026-09-15' LIMIT 1",(title,)).fetchone()
    if row:
        c.execute("UPDATE riley_reading SET companion='세이펜', summary=? WHERE id=?",(summary,row['id']))
    else:
        c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,language,genre,'','','2026-09-15',0,summary,datetime.now().isoformat(timespec='seconds'),'혜온','세이펜'))
c.commit(); c.close()
print('Hyeon Sep15 reading saved: 3 / 세이펜')