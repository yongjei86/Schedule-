import os, sqlite3

DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB)
c.row_factory=sqlite3.Row

cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
if 'read_date' not in cols:
    c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')

confirmed_dates={
    'The Worst Witch':'2026-06-22',
    '이상한 과자 가게 전천당 19':'2026-09-13',
}

# Add the confirmed read if it is not already present.
title='이상한 과자 가게 전천당 19'
if not c.execute('SELECT 1 FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone():
    rcols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
    fields=['title','language','rating','summary','created_at']
    values=[title,'한글',0,'','2026-09-13T21:00:00']
    if 'genre' in rcols:
        fields.append('genre'); values.append('창작')
    if 'sr_score' in rcols:
        fields.append('sr_score'); values.append('')
    if 'lexile_score' in rcols:
        fields.append('lexile_score'); values.append('')
    if 'read_date' in rcols:
        fields.append('read_date'); values.append('2026-09-13')
    q=','.join('?' for _ in fields)
    c.execute(f"INSERT INTO riley_reading({','.join(fields)}) VALUES({q})",values)

for title, read_date in confirmed_dates.items():
    c.execute("UPDATE riley_reading SET read_date=? WHERE title=? AND COALESCE(read_date,'')=''",(read_date,title))
    row=c.execute('SELECT id,summary FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
    if row:
        summary=(row['summary'] or '').strip()
        marker=f'읽은 날짜: {read_date}'
        if marker not in summary:
            summary=(summary+' · ' if summary else '')+marker
            c.execute('UPDATE riley_reading SET summary=? WHERE id=?',(summary,row['id']))

c.commit(); c.close()
print('Riley reading dates migrated')
