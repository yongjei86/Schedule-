import os, sqlite3

DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB)
c.row_factory=sqlite3.Row

cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
if 'read_date' not in cols:
    c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')

books=[
    ('이상한 과자 가게 전천당 19','한글','창작','2026-09-13','',''),
    ('룰스: 단 한 사람만을 위한 규칙','한글','성장','2026-09-15','',''),
    ('황금성','한글','성장','2026-09-15','',''),
    ('A Little Princess','영어','고전','2026-09-09','3.7','640L'),
    ('Robin Hood','영어','고전','2026-09-15','3.7','640L'),
    ('엄마가 사라진 어느 날','한글','성장','2026-09-16','',''),
    ('이상한 과자 가게 전천당 18','한글','창작','2026-09-17','',''),
    ('편의점을 털어라! 지리편','한글','지리','2026-09-17','',''),
    ('산불에서 코알라를 구하라!','한글','과학','2026-09-17','',''),
    ('The Canterville Ghost','영어','고전','2026-09-19','3.7','550L'),
    ('Hamlet','영어','고전','2026-09-19','','480L'),
    ('Treasure Island','영어','고전','2026-09-19','3.8','670L'),
    ('최범식간에 지구를 구하는 법','한글','창작','2026-09-20','',''),
    ('어느 날 앱에 접속했습니다','한글','창작','2026-09-20','',''),
    ('편의점을 털어라! 인체편','한글','과학','2026-09-20','',''),
    ('나도 덕후가 되고 싶어','한글','창작','2026-09-20','',''),
    ('마지막 지도 제작자: 세상의 끝을 찾아서','한글','역사','2026-09-20','',''),
    ('신상문구점','한글','창작','2026-09-22','',''),
    ('The Railway Children','영어','고전','2026-09-23','3.6','640L'),
    ('The Secret Garden','영어','고전','2026-09-23','3.4','630L'),
    ('The Adventures of King Arthur','영어','고전','2026-09-22','3.6','530L'),
    ('Romeo & Juliet','영어','고전','2026-09-25','3.5','490L'),
    ('행운이 구르는 속도','한글','창작','2026-09-24','',''),
]

rcols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
for title,language,genre,read_date,sr_score,lexile_score in books:
    row=c.execute('SELECT id FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
    if not row:
        fields=['title','language','rating','summary','created_at']
        values=[title,language,0,'',read_date+'T21:00:00']
        if 'genre' in rcols: fields.append('genre'); values.append(genre)
        if 'sr_score' in rcols: fields.append('sr_score'); values.append(sr_score)
        if 'lexile_score' in rcols: fields.append('lexile_score'); values.append(lexile_score)
        if 'read_date' in rcols: fields.append('read_date'); values.append(read_date)
        q=','.join('?' for _ in fields)
        c.execute(f"INSERT INTO riley_reading({','.join(fields)}) VALUES({q})",values)
    else:
        updates=[]; vals=[]
        if 'read_date' in rcols:
            updates.append("read_date=CASE WHEN COALESCE(read_date,'')='' THEN ? ELSE read_date END"); vals.append(read_date)
        if 'sr_score' in rcols and sr_score:
            updates.append("sr_score=CASE WHEN COALESCE(sr_score,'')='' THEN ? ELSE sr_score END"); vals.append(sr_score)
        if 'lexile_score' in rcols and lexile_score:
            updates.append("lexile_score=CASE WHEN COALESCE(lexile_score,'')='' THEN ? ELSE lexile_score END"); vals.append(lexile_score)
        if updates:
            vals.append(row['id']); c.execute('UPDATE riley_reading SET '+','.join(updates)+' WHERE id=?',vals)

confirmed_dates={'The Worst Witch':'2026-06-22'}
for title,read_date in confirmed_dates.items():
    c.execute("UPDATE riley_reading SET read_date=? WHERE title=? AND COALESCE(read_date,'')=''",(read_date,title))

c.commit(); c.close()
print('Riley reading dates and levels migrated')
