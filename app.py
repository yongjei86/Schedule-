import os, sqlite3, calendar
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','change-me')
DB_PATH = os.getenv('DB_PATH','/tmp/family_travel.db')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD','admin')

SEED = [
('2013-08-05','2013-08-09','홍콩','해외','가족여행','부부','4박 5일'),
('2013-12-24','2013-12-28','방콕','해외','가족여행','부부','4박 5일'),
('2014-08-15','2014-08-24','체코 · 오스트리아 · 헝가리','해외','가족여행','부부','9박 10일'),
('2015-01-01','2015-01-05','타이베이','해외','가족여행','부부','4박 5일'),
('2015-05-10','2015-05-17','하와이','해외','신혼여행','부부','6박 8일'),
('2015-10-01','2015-10-04','상하이','해외','가족여행','부부','3박 4일'),
('2015-12-25','2016-01-03','스페인','해외','가족여행','부부','약 9박 10일'),
('2016-02-27','2016-03-01','제주','국내','가족여행','부부','3박 4일'),
('2017-09-30','2017-10-03','속초 롯데리조트','국내','가족여행','가족 3명','약 3박 4일'),
('2018-01-01','2018-01-01','시그니엘 서울','국내','호캉스','가족 3명','날짜 확인 중'),
('2018-03-14','2018-03-17','마카오 · 홍콩','해외','가족여행','가족 3명','갤럭시 마카오 2박 + 홍콩 디즈니랜드'),
('2018-04-29','2018-05-01','제주','국내','가족여행','가족 3명','2박 3일'),
('2018-06-01','2018-06-06','괌','해외','가족여행','가족 3명','출발일 확인 중 · 6/6 귀국'),
('2018-10-09','2018-10-13','다낭','해외','가족여행','가족 3명','4박 5일'),
('2018-11-06','2018-11-09','홍콩','해외','출장+가족동반','가족 3명','3박 4일'),
('2019-06-05','2019-06-08','도쿄 · 디즈니','해외','가족여행','가족 3명','3박 4일'),
('2019-08-16','2019-08-21','다낭 · 랑코','해외','가족여행','가족 3명','5박 6일'),
('2019-11-01','2019-11-03','타이베이','해외','가족여행','가족 3명','2박 3일'),
('2020-01-09','2020-01-14','방콕','해외','가족여행','가족 3명','5박 6일'),
('2020-10-02','2020-10-03','더 스테이 힐링파크','국내','가족여행','가족 3명','날짜 추정'),
('2020-10-10','2020-10-10','몬드리안 서울','국내','호캉스','가족 3명','숙박일 확인 중'),
('2021-01-17','2021-01-18','콘래드 서울','국내','호캉스','가족 3명','1박 2일'),
('2021-04-24','2021-04-25','그랜드 하얏트 서울','국내','호캉스','가족 3명','약 1박 2일'),
('2021-05-19','2021-05-21','파크로쉬','국내','가족여행','가족 3명','2박 3일'),
('2021-08-15','2021-08-16','경원재','국내','가족여행','가족 3명','1박 2일'),
('2022-08-02','2022-08-05','파크로쉬','국내','가족여행','가족 3명','시작일 재확인 필요'),
('2022-08-14','2022-08-15','포시즌스 서울','국내','호캉스','가족 3명','1박 2일'),
('2022-10-09','2022-10-10','페어몬트 서울','국내','호캉스','가족 3명','체크인 날짜 확인 중'),
('2022-10-29','2022-10-30','가평 마이다스','국내','가족여행','가족 3명','1박 2일'),
('2022-12-26','2022-12-30','후쿠오카 · 벳푸','해외','가족여행','가족 3명','4박 5일'),
('2023-02-27','2023-03-01','켄싱턴 설악밸리','국내','가족여행','가족 4명','2박 3일'),
('2023-03-18','2023-03-19','이천 에덴파라다이스','국내','가족여행','가족 4명','1박 2일'),
('2023-08-29','2023-09-02','다낭 · 랑코','해외','가족여행','가족 4명','4박 5일'),
('2023-10-28','2023-10-29','가평 마이다스','국내','가족여행','가족 4명','1박 2일'),
('2023-12-26','2023-12-29','레스트리 리솜','국내','가족여행','가족 4명','3박 4일'),
('2024-02-29','2024-03-03','오사카','해외','가족여행','가족 4명','3박 4일'),
('2024-06-06','2024-06-09','마카오','해외','가족여행','가족 4명','3박 4일'),
('2024-07-21','2024-07-27','홋카이도','해외','가족여행','가족 4명','6박 7일'),
('2024-08-31','2024-09-01','오크밸리','국내','가족여행','가족 4명','1박 2일'),
('2024-11-09','2024-11-10','더 스테이 힐링파크','국내','가족여행','가족 4명','1박 2일'),
('2024-12-24','2024-12-27','홍콩','해외','가족여행','가족 4명','3박 4일'),
('2025-02-08','2025-02-15','발리','해외','가족여행','가족 4명','7박 8일'),
('2025-06-03','2025-06-07','제주','국내','가족여행','가족 4명','4박 5일'),
('2025-07-12','2025-07-13','오크밸리','국내','가족여행','가족 4명','1박 2일'),
('2025-08-09','2025-08-11','카시아 속초','국내','가족여행','가족 4명','2박 3일'),
('2025-10-18','2025-10-20','카시아 속초','국내','가족여행','가족 4명','2박 3일'),
('2026-01-24','2026-01-25','비발디파크','국내','가족여행','가족 4명','1박 2일'),
('2026-03-21','2026-03-22','비발디파크','국내','가족여행','가족 4명','1박 2일'),
('2026-05-23','2026-05-25','경주 코모도','국내','가족여행','가족 4명','2박 3일'),
('2026-06-20','2026-06-21','평창 켄싱턴','국내','가족여행','가족 4명','1박 2일'),
('2026-08-08','2026-08-17','발리','해외','가족여행','가족 4명','9박 10일'),
('2026-11-14','2026-11-15','롯데리조트 부여','국내','예정','가족 4명','1박 2일'),
('2027-01-02','2027-01-23','이탈리아 · 스페인','해외','예정','가족 4명','약 3주'),
('2027-08-07','2027-08-15','싱가포르 · Disney Adventure','해외','검토 중','가족 4명','8/9~12 크루즈'),
('2028-01-01','2028-12-31','호주','해외','장기 계획','가족 4명','시드니 + 자연·동물 체험'),
('2029-01-01','2029-12-31','미국 서부','해외','장기 계획','가족 4명','SF · 요세미티 · LA'),
('2030-01-01','2030-12-31','중부유럽','해외','장기 계획','가족 4명','프라하 · 빈 · 부다페스트')
]

CSS='''
:root{--bg:#f6f8fb;--card:#fff;--ink:#10233c;--muted:#6b7a90;--line:#e5eaf0;--blue:#0f4c81;--soft:#edf4fb;--red:#b74b4b;--green:#2d7b58}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}.wrap{max-width:1180px;margin:auto;padding:20px}header{position:sticky;top:0;z-index:5;background:rgba(246,248,251,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}nav{max-width:1180px;margin:auto;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;gap:12px}.brand{font-weight:900}nav .links{display:flex;gap:8px;flex-wrap:wrap}nav a{padding:8px 10px;border-radius:10px;text-decoration:none;color:var(--muted)}nav a:hover{background:#fff;color:var(--blue)}.hero{background:linear-gradient(145deg,#0f4c81,#173d66);color:white;padding:28px;border-radius:24px;margin:22px 0}.hero h1{margin:0;font-size:38px}.hero p{opacity:.85}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px}.year{font-size:12px;color:var(--blue);font-weight:800}.dest{font-size:20px;font-weight:850;margin:5px 0}.muted{color:var(--muted);font-size:14px}.pill{display:inline-block;padding:5px 8px;border-radius:999px;background:var(--soft);color:var(--blue);font-size:12px;font-weight:700}.section{margin-top:28px}.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.filters a{background:#fff;border:1px solid var(--line);padding:8px 10px;border-radius:10px;text-decoration:none;color:var(--ink)}table{width:100%;border-collapse:separate;border-spacing:0;background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden}th,td{padding:11px;border-bottom:1px solid var(--line);text-align:left;font-size:14px}th{background:#fbfcfe;color:var(--muted)}tr:last-child td{border-bottom:0}.btn{display:inline-block;background:var(--blue);color:#fff;padding:9px 12px;border-radius:10px;text-decoration:none;border:0}.btn.secondary{background:#fff;color:var(--ink);border:1px solid var(--line)}.btn.danger{background:var(--red)}form{display:grid;gap:12px}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}input,select,textarea{width:100%;padding:11px;border:1px solid #cfd7e2;border-radius:10px;background:#fff;font:inherit}label{font-size:13px;color:var(--muted)}.calendar-head{display:flex;justify-content:space-between;align-items:center;gap:10px}.months{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.month{background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px}.month h3{text-align:center;margin:3px 0 10px}.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}.dow,.day{text-align:center;font-size:12px;padding:6px 2px}.dow{color:var(--muted);font-weight:700}.day{border-radius:8px;min-height:32px}.day.has{background:var(--soft);color:var(--blue);font-weight:800}.events{margin-top:10px;font-size:12px}.event{padding:7px;background:#f8fafc;border-radius:8px;margin-top:5px}.flash{padding:10px 12px;background:#eaf7ef;color:var(--green);border-radius:10px;margin:12px 0}@media(max-width:850px){.grid,.months{grid-template-columns:1fr 1fr}}@media(max-width:600px){.grid,.months,.row{grid-template-columns:1fr}.hero h1{font-size:30px}nav .links{display:none}table{font-size:12px}th,td{padding:8px}.hide-mobile{display:none}}
'''

def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row; return con

def init_db():
    con=db(); cur=con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS trips(id INTEGER PRIMARY KEY AUTOINCREMENT,start_date TEXT,end_date TEXT,destination TEXT,region TEXT,status TEXT,party TEXT,notes TEXT)''')
    if cur.execute('SELECT COUNT(*) FROM trips').fetchone()[0]==0:
        cur.executemany('INSERT INTO trips(start_date,end_date,destination,region,status,party,notes) VALUES(?,?,?,?,?,?,?)',SEED)
    con.commit(); con.close()

init_db()

def layout(title,body):
    flashes=''.join(f'<div class="flash">{m}</div>' for m in session.pop('_flashes',[]) )
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header><nav><a class="brand" href="/">✈️ 우리 가족 여행</a><div class="links"><a href="/history">과거 여행</a><a href="/plans">예정 여행</a><a href="/calendar">가족 달력</a><a href="/admin">관리자</a></div></nav></header><main class="wrap">{flashes}{body}</main></body></html>'''

def qtrips(where='',params=()):
    con=db(); rows=con.execute('SELECT * FROM trips '+where+' ORDER BY start_date',params).fetchall(); con.close(); return rows

@app.route('/')
def home():
    future=qtrips("WHERE start_date >= date('now')")
    history=qtrips("WHERE start_date < date('now')")
    cards=''.join(f'''<div class="card"><div class="year">{r['start_date'][:4]}</div><div class="dest">{r['destination']}</div><span class="pill">{r['status']}</span><p class="muted">{r['start_date']} ~ {r['end_date']}<br>{r['notes']}</p></div>''' for r in future[:6])
    body=f'''<section class="hero"><h1>우리 가족 여행 기록</h1><p>지나온 여행과 앞으로의 여행을 한곳에서 보고, 가족 달력으로 일정까지 관리합니다.</p></section><section class="section"><h2>앞으로의 여행</h2><div class="grid">{cards}</div></section><section class="section"><div class="grid"><div class="card"><div class="muted">기록된 여행</div><div class="dest">{len(history)}회</div></div><div class="card"><div class="muted">예정·장기 계획</div><div class="dest">{len(future)}개</div></div><div class="card"><div class="muted">기록 시작</div><div class="dest">2013년</div></div></div></section>'''
    return layout('우리 가족 여행',body)

@app.route('/history')
def history():
    year=request.args.get('year',''); region=request.args.get('region','')
    sql="WHERE start_date < date('now')"; p=[]
    if year: sql+=' AND substr(start_date,1,4)=?'; p.append(year)
    if region: sql+=' AND region=?'; p.append(region)
    rows=qtrips(sql,tuple(p))
    years=sorted({r['start_date'][:4] for r in qtrips("WHERE start_date < date('now')")},reverse=True)
    filt='<div class="filters"><a href="/history">전체</a>'+''.join(f'<a href="/history?year={y}">{y}</a>' for y in years)+'</div>'
    trs=''.join(f"<tr><td>{r['start_date']}</td><td>{r['destination']}</td><td>{r['region']}</td><td>{r['party']}</td><td>{r['notes']}</td></tr>" for r in rows)
    return layout('과거 여행',f'''<h1>과거 여행</h1>{filt}<table><tr><th>출발</th><th>여행지</th><th>구분</th><th class="hide-mobile">구성</th><th>메모</th></tr>{trs}</table>''')

@app.route('/plans')
def plans():
    rows=qtrips("WHERE start_date >= date('now')")
    cards=''.join(f'''<div class="card"><div class="year">{r['start_date']} ~ {r['end_date']}</div><div class="dest">{r['destination']}</div><span class="pill">{r['status']}</span><p class="muted">{r['party']}<br>{r['notes']}</p></div>''' for r in rows)
    return layout('예정 여행',f'<h1>예정 여행</h1><div class="grid">{cards}</div>')

@app.route('/calendar')
def family_calendar():
    year=int(request.args.get('year',datetime.now().year))
    rows=qtrips('WHERE substr(start_date,1,4)=? OR substr(end_date,1,4)=?',(str(year),str(year)))
    month_html=[]
    for m in range(1,13):
        cal=calendar.Calendar(firstweekday=0)
        weeks=cal.monthdayscalendar(year,m)
        days=[]
        for d in ['월','화','수','목','금','토','일']: days.append(f'<div class="dow">{d}</div>')
        mev=[]
        for r in rows:
            try:
                s=datetime.fromisoformat(r['start_date']).date(); e=datetime.fromisoformat(r['end_date']).date()
            except: continue
            if s.year==year and s.month==m or e.year==year and e.month==m or (s <= datetime(year,m,15).date() <= e): mev.append(r)
        for wk in weeks:
            for d in wk:
                if d==0: days.append('<div class="day"></div>'); continue
                dt=datetime(year,m,d).date(); hit=any(datetime.fromisoformat(r['start_date']).date()<=dt<=datetime.fromisoformat(r['end_date']).date() for r in rows)
                days.append(f'<div class="day {"has" if hit else ""}">{d}</div>')
        ev=''.join(f'<div class="event">{r["destination"]}<br>{r["start_date"]}~{r["end_date"]}</div>' for r in mev)
        month_html.append(f'<div class="month"><h3>{m}월</h3><div class="cal">{"".join(days)}</div><div class="events">{ev}</div></div>')
    body=f'''<div class="calendar-head"><h1>가족 달력 · {year}</h1><div><a class="btn secondary" href="/calendar?year={year-1}">← {year-1}</a> <a class="btn secondary" href="/calendar?year={year+1}">{year+1} →</a></div></div><div class="months">{"".join(month_html)}</div>'''
    return layout('가족 달력',body)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form.get('password')==ADMIN_PASSWORD:
            session['admin']=True; return redirect('/admin')
        flash('비밀번호가 맞지 않습니다.')
    return layout('관리자 로그인','''<h1>관리자 로그인</h1><div class="card" style="max-width:420px"><form method="post"><label>비밀번호</label><input type="password" name="password" required><button class="btn">로그인</button></form></div>''')

def guard():
    return session.get('admin')

@app.route('/admin')
def admin():
    if not guard(): return redirect('/login')
    rows=qtrips()
    trs=''.join(f'''<tr><td>{r['start_date']}</td><td>{r['destination']}</td><td>{r['status']}</td><td><a class="btn secondary" href="/admin/edit/{r['id']}">수정</a> <form style="display:inline" method="post" action="/admin/delete/{r['id']}" onsubmit="return confirm('삭제할까요?')"><button class="btn danger">삭제</button></form></td></tr>''' for r in rows)
    return layout('관리자',f'''<div class="calendar-head"><h1>여행 관리</h1><a class="btn" href="/admin/new">+ 여행 추가</a></div><table><tr><th>날짜</th><th>여행지</th><th>상태</th><th>관리</th></tr>{trs}</table>''')

def form_page(r=None):
    g=lambda k: (r[k] if r else '')
    return f'''<form method="post"><div class="row"><div><label>출발일</label><input type="date" name="start_date" value="{g('start_date')}" required></div><div><label>도착일</label><input type="date" name="end_date" value="{g('end_date')}" required></div></div><label>여행지</label><input name="destination" value="{g('destination')}" required><div class="row"><div><label>국내/해외</label><select name="region"><option {'selected' if g('region')=='국내' else ''}>국내</option><option {'selected' if g('region')=='해외' else ''}>해외</option></select></div><div><label>상태</label><input name="status" value="{g('status')}" placeholder="가족여행 / 예정 / 검토 중"></div></div><label>가족 구성</label><input name="party" value="{g('party')}"><label>메모</label><textarea name="notes" rows="4">{g('notes')}</textarea><button class="btn">저장</button></form>'''

@app.route('/admin/new',methods=['GET','POST'])
def admin_new():
    if not guard(): return redirect('/login')
    if request.method=='POST':
        con=db(); con.execute('INSERT INTO trips(start_date,end_date,destination,region,status,party,notes) VALUES(?,?,?,?,?,?,?)',tuple(request.form.get(k,'') for k in ['start_date','end_date','destination','region','status','party','notes'])); con.commit(); con.close(); flash('추가했습니다.'); return redirect('/admin')
    return layout('여행 추가','<h1>여행 추가</h1><div class="card">'+form_page()+'</div>')

@app.route('/admin/edit/<int:i>',methods=['GET','POST'])
def admin_edit(i):
    if not guard(): return redirect('/login')
    con=db(); r=con.execute('SELECT * FROM trips WHERE id=?',(i,)).fetchone()
    if request.method=='POST':
        vals=[request.form.get(k,'') for k in ['start_date','end_date','destination','region','status','party','notes']]+[i]
        con.execute('UPDATE trips SET start_date=?,end_date=?,destination=?,region=?,status=?,party=?,notes=? WHERE id=?',vals); con.commit(); con.close(); flash('수정했습니다.'); return redirect('/admin')
    con.close(); return layout('여행 수정','<h1>여행 수정</h1><div class="card">'+form_page(r)+'</div>')

@app.route('/admin/delete/<int:i>',methods=['POST'])
def admin_delete(i):
    if not guard(): return redirect('/login')
    con=db(); con.execute('DELETE FROM trips WHERE id=?',(i,)); con.commit(); con.close(); flash('삭제했습니다.'); return redirect('/admin')

@app.route('/health')
def health(): return jsonify(ok=True)

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))
