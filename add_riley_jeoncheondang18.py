import os, sqlite3
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
c.commit(); c.close()
print('Added/updated Riley reading:', title)
