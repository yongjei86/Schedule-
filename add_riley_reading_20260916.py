import os, sqlite3
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo('Asia/Seoul')
except Exception:
    KST = None

DB = os.getenv('DB_PATH', '/data/family_travel.db')
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
cols = {r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}

# Keep this migration-safe for older deployed databases.
if 'read_date' not in cols:
    c.execute('ALTER TABLE riley_reading ADD COLUMN read_date TEXT')
    cols.add('read_date')
if 'child' not in cols:
    c.execute("ALTER TABLE riley_reading ADD COLUMN child TEXT DEFAULT '지유'")
    cols.add('child')

books = [
    {
        'title': '산불에서 코알라를 구하라!',
        'language': '한글',
        'genre': '지식',
        'summary': '우리는 글로벌 히어로즈 1 · 산불과 야생동물 구조를 다룬 이야기',
    },
    {
        'title': '편의점을 털어라! 지리편',
        'language': '한글',
        'genre': '지식',
        'summary': '편의점 속 상품과 일상을 소재로 배우는 지리 지식',
    },
]
read_date = '2026-09-16'
created_at = '2026-09-16T20:00:00'

for book in books:
    row = c.execute(
        "SELECT id FROM riley_reading WHERE child='지유' AND title=? AND read_date=? LIMIT 1",
        (book['title'], read_date),
    ).fetchone()
    if row:
        c.execute(
            "UPDATE riley_reading SET language=?, genre=?, summary=? WHERE id=?",
            (book['language'], book['genre'], book['summary'], row['id']),
        )
    else:
        fields = ['title', 'language', 'rating', 'summary', 'created_at', 'child', 'read_date']
        vals = [book['title'], book['language'], 0, book['summary'], created_at, '지유', read_date]
        if 'genre' in cols:
            fields.append('genre'); vals.append(book['genre'])
        if 'sr_score' in cols:
            fields.append('sr_score'); vals.append('')
        if 'lexile_score' in cols:
            fields.append('lexile_score'); vals.append('')
        q = ','.join('?' for _ in fields)
        c.execute(f"INSERT INTO riley_reading({','.join(fields)}) VALUES({q})", vals)

# Direct DB inserts bypass the normal route that awards +3 credits per book.
c.execute('''CREATE TABLE IF NOT EXISTS riley_credits(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  child TEXT NOT NULL,
  delta INTEGER NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
)''')
for book in books:
    credit_reason = f"독서 기록 추가: {book['title']}"
    already = c.execute('SELECT id FROM riley_credits WHERE reason=? LIMIT 1', (credit_reason,)).fetchone()
    if not already:
        now = datetime.now(KST).isoformat(timespec='seconds') if KST else datetime.now().isoformat(timespec='seconds')
        c.execute(
            'INSERT INTO riley_credits(child,delta,reason,created_at) VALUES(?,?,?,?)',
            ('지유', 3, credit_reason, now),
        )

c.commit()
c.close()
print('Riley Sep16 reading saved: 2 books')
