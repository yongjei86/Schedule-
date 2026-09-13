import os, sqlite3
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo('Asia/Seoul')
except Exception:
    KST = None
DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
if 'read_date' not in cols:
    c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')
    cols.add('read_date')
title='이상한 과자 가게 전천당 18'
row=c.execute('SELECT id FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
if row:
    c.execute("UPDATE riley_reading SET language='한글', genre='창작', read_date=? WHERE id=?",('2026-09-13',row['id']))
else:
    fields=['title','language','rating','summary','created_at']
    vals=[title,'한글',0,'','2026-09-13T18:29:00']
    if 'genre' in cols:
        fields.append('genre'); vals.append('창작')
    if 'sr_score' in cols:
        fields.append('sr_score'); vals.append('')
    if 'lexile_score' in cols:
        fields.append('lexile_score'); vals.append('')
    if 'read_date' in cols:
        fields.append('read_date'); vals.append('2026-09-13')
    q=','.join('?' for _ in fields)
    c.execute(f"INSERT INTO riley_reading({','.join(fields)}) VALUES({q})",vals)

# This script inserts directly into riley_reading, bypassing the normal
# /riley/reading/add route that awards +3 credits per book. Award it here
# once, guarded so re-running this script on every deploy doesn't double-credit.
c.execute('''CREATE TABLE IF NOT EXISTS riley_credits(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  child TEXT NOT NULL,
  delta INTEGER NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
)''')
credit_reason=f'독서 기록 추가: {title}'
already=c.execute('SELECT id FROM riley_credits WHERE reason=? LIMIT 1',(credit_reason,)).fetchone()
if not already:
    now=datetime.now(KST).isoformat(timespec='seconds') if KST else datetime.now().isoformat(timespec='seconds')
    c.execute('insert into riley_credits(child,delta,reason,created_at) values(?,?,?,?)',('지유',3,credit_reason,now))
    print('Awarded 3 credits for:', title)

c.commit(); c.close()
print('Added/updated Riley reading:', title)
