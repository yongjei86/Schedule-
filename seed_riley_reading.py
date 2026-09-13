import os, sqlite3
from datetime import datetime

DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
c.execute('''CREATE TABLE IF NOT EXISTS riley_reading(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,language TEXT,rating INTEGER DEFAULT 0,summary TEXT,created_at TEXT NOT NULL,genre TEXT,sr_score TEXT,lexile_score TEXT)''')
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
for name in ('genre','sr_score','lexile_score'):
    if name not in cols:
        c.execute(f'ALTER TABLE riley_reading ADD COLUMN {name} TEXT')

books=[
('The Miraculous Journey of Edward Tulane','영어','창작','4.4','700L'),
("Charlotte's Web",'영어','창작','4.4','680L'),
('Shiloh','영어','창작','4.4','890L'),
('Holes','영어','창작','4.6','660L'),
('The Breadwinner','영어','역사','4.5','710L'),
('Turtle in Paradise','영어','역사','3.7','610L'),
('The Worst Witch','영어','창작','5.4','890L'),
('The Phoenix of Destiny','영어','창작','4.8','690L'),
('The Magic Finger','영어','창작','3.1','560L'),
('The Giraffe and the Pelly and Me','영어','창작','4.7','840L'),
('The Twits','영어','창작','4.4','750L'),
("My Father's Dragon",'영어','창작','5.6','970L'),
('The Bad Beginning','영어','창작','6.4','1010L'),
('Diary of a Wimpy Kid','영어','창작','5.2','950L'),
('고양이 해결사 깜냥','한글','창작','',''),
('오무라이스 잼잼','한글','만화','','')]
now=datetime.now().isoformat(timespec='seconds')
for title,language,genre,sr,lexile in books:
    row=c.execute('SELECT id FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
    if row:
        c.execute("UPDATE riley_reading SET language=CASE WHEN COALESCE(language,'')='' THEN ? ELSE language END, genre=CASE WHEN COALESCE(genre,'')='' THEN ? ELSE genre END, sr_score=CASE WHEN COALESCE(sr_score,'')='' THEN ? ELSE sr_score END, lexile_score=CASE WHEN COALESCE(lexile_score,'')='' THEN ? ELSE lexile_score END WHERE id=?",(language,genre,sr,lexile,row['id']))
    else:
        c.execute('INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,rating,summary,created_at) VALUES(?,?,?,?,?,0,?,?)',(title,language,genre,sr,lexile,'',now))
c.commit(); c.close()

import seed_hyeon_reading
