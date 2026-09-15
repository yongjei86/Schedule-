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
for day in ('화','목'):
 exists=c.execute("SELECT 1 FROM academy WHERE active=1 AND day_of_week=? AND start_time='21:00' AND REPLACE(COALESCE(academy,''),' ','') LIKE '%화상영어%' LIMIT 1",(day,)).fetchone()
 if not exists:
  c.execute("INSERT INTO academy(day_of_week,start_time,end_time,academy,subject,location,notes,active) VALUES(?,?,?,?,?,?,?,1)",(day,'21:00','','화상영어','영어','',''))
c.commit(); c.close()
import seed_riley_reading
import add_riley_jeoncheondang18
import add_hyeon_reading_20260914
import add_hyeon_waenyamyeon_20260914
import add_hyeon_winter_is_here_20260914
import add_hyeon_reading_20260915
print('SQLite schema ready:',DB)