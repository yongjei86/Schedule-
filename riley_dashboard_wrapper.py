from datetime import datetime, timedelta
from collections import Counter, defaultdict
from home_tasks_only_app import app, db, H, page, KST

DASH_CSS='''<style>
.rd-wrap{max-width:1180px;margin:auto}.rd-tabs{display:flex;gap:6px;margin:12px 0 16px;flex-wrap:wrap}.rd-tabs a{padding:8px 13px;border:1px solid #dfe6ee;border-radius:999px;text-decoration:none;color:#65758b;background:#fff}.rd-tabs a.on{background:#0f4c81;color:#fff;border-color:#0f4c81}.rd-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}.rd-kpi{background:#fff;border:1px solid #e4e9f0;border-radius:14px;padding:14px}.rd-kpi b{display:block;font-size:25px;color:#0f4c81}.rd-kpi span{font-size:12px;color:#7a8798}.rd-grid{display:grid;grid-template-columns:1.4fr .8fr;gap:12px}.rd-card{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:14px;margin-bottom:12px}.rd-row{display:grid;grid-template-columns:100px 1fr 52px;gap:10px;align-items:center;margin:9px 0}.rd-bar{height:9px;background:#eaf0f6;border-radius:99px;overflow:hidden}.rd-fill{height:100%;background:#0f4c81;border-radius:99px}.rd-book{padding:9px 0;border-bottom:1px solid #edf1f5}.rd-book:last-child{border-bottom:0}.rd-meta{font-size:12px;color:#7a8798;margin-top:3px}@media(max-width:700px){.rd-kpis{grid-template-columns:repeat(2,1fr)}.rd-grid{grid-template-columns:1fr}.rd-row{grid-template-columns:78px 1fr 40px}}
</style>'''

def _rows():
 c=db(); rows=[dict(r) for r in c.execute("select * from riley_reading where child='지유' and read_date is not null and read_date!='' order by read_date desc,id desc").fetchall()]; c.close(); return rows

def _period_key(ds,view):
 d=datetime.strptime(ds,'%Y-%m-%d').date()
 if view=='day': return d.strftime('%m/%d')
 if view=='week':
  m=d-timedelta(days=d.weekday()); return m.strftime('%m/%d')+'~'+(m+timedelta(days=6)).strftime('%m/%d')
 return d.strftime('%Y.%m')

def _num(v):
 try:return float(str(v).replace('L','').strip())
 except:return None

@app.route('/riley/reading/dashboard')
def riley_reading_dashboard():
 view=(__import__('flask').request.args.get('view') or 'week').lower()
 if view not in ('day','week','month'): view='week'
 rows=_rows(); today=datetime.now(KST).date(); mon=today-timedelta(days=today.weekday()); month=today.strftime('%Y-%m')
 today_n=sum(1 for r in rows if r['read_date']==today.isoformat())
 week_n=sum(1 for r in rows if mon.isoformat()<=r['read_date']<=(mon+timedelta(days=6)).isoformat())
 month_n=sum(1 for r in rows if r['read_date'].startswith(month))
 eng=sum(1 for r in rows if r.get('language')=='영어'); kor=sum(1 for r in rows if r.get('language')=='한글')
 grouped=Counter(_period_key(r['read_date'],view) for r in rows); items=list(grouped.items())[:31 if view=='day' else 16 if view=='week' else 12]
 mx=max([n for _,n in items] or [1])
 bars=''.join(f'<div class="rd-row"><b>{H(k)}</b><div class="rd-bar"><div class="rd-fill" style="width:{n/mx*100:.0f}%"></div></div><b>{n}권</b></div>' for k,n in items)
 recent=''
 for r in rows[:12]:
  lvl=' · '.join(x for x in [f"SR {r.get('sr_score')}" if r.get('sr_score') else '',f"Lexile {r.get('lexile_score')}" if r.get('lexile_score') else ''] if x)
  recent+=f'<div class="rd-book"><b>{H(r["title"])}</b><div class="rd-meta">{H(r["read_date"])} · {H(r.get("language") or "-")} · {H(r.get("genre") or "-")}{(" · "+H(lvl)) if lvl else ""}</div></div>'
 sr=[_num(r.get('sr_score')) for r in rows if _num(r.get('sr_score')) is not None]; lx=[_num(r.get('lexile_score')) for r in rows if _num(r.get('lexile_score')) is not None]
 levels=f'<div class="rd-card"><h3>영어 원서 레벨</h3><div class="rd-meta">등록 도서 기준</div><p><b>평균 SR {sum(sr)/len(sr):.1f}</b>' if sr else '<div class="rd-card"><h3>영어 원서 레벨</h3><p>SR 데이터 없음'
 if sr: levels+=f' · 범위 {min(sr):g}~{max(sr):g}'
 if lx: levels+=f'</p><p><b>평균 Lexile {sum(lx)/len(lx):.0f}L</b> · 범위 {min(lx):g}~{max(lx):g}L'
 levels+='</p></div>'
 tabs=''.join(f'<a class="{"on" if view==v else ""}" href="/riley/reading/dashboard?view={v}">{label}</a>' for v,label in [('day','일별'),('week','주별'),('month','월별')])
 body=DASH_CSS+f'''<div class="rd-wrap"><div class="toolbar"><div><h1 style="margin:0">지유 독서 대시보드</h1><div class="muted">읽은 날짜 기준 독서 추적</div></div><a class="btn s" href="/riley">지유 포탈</a></div><div class="rd-tabs">{tabs}</div><div class="rd-kpis"><div class="rd-kpi"><b>{today_n}</b><span>오늘</span></div><div class="rd-kpi"><b>{week_n}</b><span>이번 주</span></div><div class="rd-kpi"><b>{month_n}</b><span>이번 달</span></div><div class="rd-kpi"><b>{len(rows)}</b><span>날짜 등록 누적</span></div></div><div class="rd-grid"><div><div class="rd-card"><h3>{'일별' if view=='day' else '주별' if view=='week' else '월별'} 독서량</h3>{bars or '<div class="muted">데이터 없음</div>'}</div><div class="rd-card"><h3>최근 읽은 책</h3>{recent or '<div class="muted">데이터 없음</div>'}</div></div><div><div class="rd-card"><h3>언어 구성</h3><p><b>한글 {kor}권</b> · 영어 {eng}권</p></div>{levels}</div></div></div>'''
 return page('지유 독서 대시보드',body)

# Add a dashboard shortcut above the existing reading section without rewriting the main app.
import home_tasks_only_app as _main
_old=_main._reading_section
def _with_dashboard(child='지유',base='/riley'):
 s=_old(child,base)
 if child=='지유' and base=='/riley':
  return '<div style="display:flex;justify-content:flex-end;margin:10px 0"><a class="btn" href="/riley/reading/dashboard">독서 대시보드</a></div>'+s
 return s
_main._reading_section=_with_dashboard
