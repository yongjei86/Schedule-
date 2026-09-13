import os, sqlite3

DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB)
c.row_factory=sqlite3.Row

cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
if 'read_date' not in cols:
    c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')

# Confirmed from the 2026-06-22 conversation: Riley read The Worst Witch 1 that day.
confirmed_dates={
    'The Worst Witch':'2026-06-22',
}
for title, read_date in confirmed_dates.items():
    c.execute("UPDATE riley_reading SET read_date=? WHERE title=? AND COALESCE(read_date,'')=''",(read_date,title))
    # Surface the date in the current UI until a dedicated date field is rendered.
    row=c.execute('SELECT id,summary FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
    if row:
        summary=(row['summary'] or '').strip()
        marker=f'읽은 날짜: {read_date}'
        if marker not in summary:
            summary=(summary+' · ' if summary else '')+marker
            c.execute('UPDATE riley_reading SET summary=? WHERE id=?',(summary,row['id']))

c.commit(); c.close()
print('Riley reading dates migrated')
