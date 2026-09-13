import os, sqlite3
DB=os.getenv('DB_PATH','/data/family_travel.db')
os.makedirs(os.path.dirname(DB) or '.',exist_ok=True)
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row

def table_exists(name):
 return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None

def columns(name):
 return {r['name'] for r in c.execute(f'PRAGMA table_info({name})')}

if table_exists('trips'):
 old=columns('trips')
 for name,default in [('country',"''"),('region',"''"),('title',"''"),('companions',"''"),('trip_type',"''"),('status',"'완료'"),('lodging',"''"),('transport',"''"),('notes',"''")]:
  if name not in old:
   c.execute(f'ALTER TABLE trips ADD COLUMN {name} TEXT DEFAULT {default}')
 now=columns('trips')
 if 'destination' in now:
  c.execute("UPDATE trips SET title=COALESCE(NULLIF(title,''),destination), region=COALESCE(NULLIF(region,''),destination), country=COALESCE(NULLIF(country,''),destination)")
 if 'kind' in now:
  c.execute("UPDATE trips SET trip_type=COALESCE(NULLIF(trip_type,''),kind)")
 if 'category' in now:
  c.execute("UPDATE trips SET status=CASE WHEN category IN ('예정','검토 중','장기 계획') THEN category ELSE COALESCE(NULLIF(status,''),'완료') END")
else:
 c.execute('''CREATE TABLE trips(id INTEGER PRIMARY KEY,start_date TEXT,end_date TEXT,country TEXT,region TEXT,title TEXT,companions TEXT,trip_type TEXT,status TEXT,lodging TEXT,transport TEXT,notes TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS itinerary(id INTEGER PRIMARY KEY,trip_id INTEGER REFERENCES trips(id) ON DELETE CASCADE,item_date TEXT,day_label TEXT,time_text TEXT,title TEXT,place TEXT,detail TEXT,sort_order INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS calendar_events(id INTEGER PRIMARY KEY,start_date TEXT,end_date TEXT,title TEXT,category TEXT,person TEXT,notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS academy(id INTEGER PRIMARY KEY,day_of_week TEXT,start_time TEXT,end_time TEXT,academy TEXT,subject TEXT,location TEXT,notes TEXT,active INTEGER DEFAULT 1)''')

# Riley's fixed video-English schedule is persisted locally as a fallback.
# The weekly view already deduplicates it when the same Google recurring event exists.
for day in ('화','목'):
 exists=c.execute("SELECT 1 FROM academy WHERE active=1 AND day_of_week=? AND start_time='21:00' AND REPLACE(COALESCE(academy,''),' ','') LIKE '%화상영어%' LIMIT 1",(day,)).fetchone()
 if not exists:
  c.execute("INSERT INTO academy(day_of_week,start_time,end_time,academy,subject,location,notes,active) VALUES(?,?,?,?,?,?,?,1)",(day,'21:00','','화상영어','영어','',''))

# Riley reading DB: keep the app schema compatible and seed only confirmed reads.
c.execute('''CREATE TABLE IF NOT EXISTS riley_reading(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 language TEXT,
 rating INTEGER DEFAULT 0,
 summary TEXT,
 created_at TEXT NOT NULL,
 genre TEXT,
 level_score TEXT
)''')
rcols=columns('riley_reading')
if 'genre' not in rcols:
 c.execute('ALTER TABLE riley_reading ADD COLUMN genre TEXT')
if 'level_score' not in rcols:
 c.execute('ALTER TABLE riley_reading ADD COLUMN level_score TEXT')

READING_SEED=[
 ('The Miraculous Journey of Edward Tulane','영어','창작','SR 4.4 · Lexile 700L'),
 ("Charlotte's Web",'영어','창작','SR 4.4 · Lexile 680L'),
 ('Shiloh','영어','창작','SR 4.4 · Lexile 890L'),
 ('Holes','영어','창작','SR 4.6 · Lexile 660L'),
 ('The Breadwinner','영어','역사','SR 4.5 · Lexile 710L'),
 ('Turtle in Paradise','영어','역사','SR 3.7 · Lexile 610L'),
 ('The Worst Witch','영어','창작','SR 5.4 · Lexile 890L'),
 ('The Phoenix of Destiny','영어','창작','SR 4.8 · Lexile 690L'),
 ('The Magic Finger','영어','창작','SR 3.1 · Lexile 560L'),
 ('The Giraffe and the Pelly and Me','영어','창작','SR 4.7 · Lexile 840L'),
 ('The Twits','영어','창작','SR 4.4 · Lexile 750L'),
 ("My Father's Dragon",'영어','창작','SR 5.6 · Lexile 970L'),
 ('The Bad Beginning','영어','창작','SR 6.4 · Lexile 1010L'),
 ('Diary of a Wimpy Kid','영어','창작','SR 5.2 · Lexile 950L'),
 ('고양이 해결사 깜냥','한글','창작',''),
 ('오무라이스 잼잼','한글','만화','')
]
now='2026-09-13T15:30:00'
for title,language,genre,level_score in READING_SEED:
 exists=c.execute('SELECT 1 FROM riley_reading WHERE title=? LIMIT 1',(title,)).fetchone()
 if not exists:
  c.execute('INSERT INTO riley_reading(title,language,genre,level_score,rating,summary,created_at) VALUES(?,?,?,?,0,?,?)',(title,language,genre,level_score,'',now))

c.commit(); c.close()
print('SQLite schema ready:',DB)