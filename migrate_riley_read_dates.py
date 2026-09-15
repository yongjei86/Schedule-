import os, sqlite3

DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB)
c.row_factory=sqlite3.Row

cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
if 'read_date' not in cols:
    c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')

books=[
    ('이상한 과자 가게 전천당 19','한글','창작','2026-09-13'),
    ('룰스: 단 한 사람만을 위한 규칙','한글','성장','2026-09-15'),
    ('황금성','한글','성장','2026-09-15'),
    ('A Little Princess','영어','고전','2026-09-09'),
]

rcols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
for title,language,genre,read_date in books:
    row=c.execute('SELECT id FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
    if not row:
        fields=['title','language','rating','summary','created_at']
        values=[title,language,0,'',read_date+'T21:00:00']
        if 'genre' in rcols:
            fields.append('genre'); values.append(genre)
        if 'sr_score' in rcols:
            fields.append('sr_score'); values.append('')
        if 'lexile_score' in rcols:
            fields.append('lexile_score'); values.append('')
        if 'read_date' in rcols:
            fields.append('read_date'); values.append(read_date)
        q=','.join('?' for _ in fields)
        c.execute(f"INSERT INTO riley_reading({','.join(fields)}) VALUES({q})",values)
    else:
        c.execute("UPDATE riley_reading SET read_date=? WHERE id=? AND COALESCE(read_date,'')=''",(read_date,row['id']))

confirmed_dates={'The Worst Witch':'2026-06-22'}
for title,read_date in confirmed_dates.items():
    c.execute("UPDATE riley_reading SET read_date=? WHERE title=? AND COALESCE(read_date,'')=''",(read_date,title))

c.commit(); c.close()
print('Riley reading dates migrated')
