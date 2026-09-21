import os, sqlite3
from datetime import datetime
DB=os.getenv('DB_PATH','/data/family_travel.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
cols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)')}
if 'companion' not in cols:
    c.execute("ALTER TABLE riley_reading ADD COLUMN companion TEXT DEFAULT ''")

books=[
('2026-09-16',"Let's Hold an Open Day Show!",'영어','리더스','Disney English Reading Club Sight Words Book 9','아빠'),
('2026-09-16','What Is a Friend?','영어','리더스','Disney Reading Adventures Level 1','아빠'),
('2026-09-16',"Belle's Wedding Day",'영어','리더스','Disney Reading Adventures Level 1','아빠'),
('2026-09-16','Family','영어','리더스','Disney Reading Adventures Level 1','아빠'),
('2026-09-16','In the Castle','영어','리더스','Disney Reading Adventures Level 1','아빠'),
('2026-09-17','와글와글 동물들이 많아졌어요','한국어','지식','동물 관찰·찾기','아빠'),
('2026-09-17','밤하늘에 톡톡톡','한국어','수학','수학동화 8 · 수','아빠'),
('2026-09-17','도도 공주의 생일 케이크','한국어','수학','수학동화 10 · 측정 · 글 서동선 · 그림 윤이나','아빠'),
('2026-09-18','This Pumpkin','영어','과학','Scholastic Guided Science Readers A','아빠'),
('2026-09-18','What Can I See?','영어','리더스','Scholastic First Little Readers A · Deborah Schecter','아빠'),
('2026-09-18','A Bunny Can Hop','영어','과학','Scholastic Guided Science Readers A','아빠'),
('2026-09-18','My Pet Rock','영어','리더스','Scholastic First Little Comics A+ · Liza Charlesworth','아빠'),
('2026-09-18','Super Mouse','영어','리더스','Scholastic First Little Comics A · Liza Charlesworth','아빠'),
('2026-09-18','왜 약속을 안 지키면 안 돼요?','한국어','지식','생활습관 · 사회성','아빠'),
('2026-09-18','왜 예방 주사를 맞아야 돼요?','한국어','지식','몸 · 건강 지식','아빠'),
('2026-09-18','왜 양치질을 해야 돼요?','한국어','지식','몸 · 건강 · 생활습관','아빠'),
('2026-09-18','왜 커피 마시면 안 돼요?','한국어','지식','몸 · 건강 · 생활습관','아빠'),
('2026-09-18','왜 늦게 자면 안 돼요?','한국어','지식','수면 · 건강 · 생활습관','아빠'),
('2026-09-19','소피아가 둘이야!','한국어','창작','Disney 리틀 프린세스 소피아','혼자'),
('2026-09-19','볼트','한국어','창작','Disney 골든 명작','아빠'),
('2026-09-19','정글북','한국어','창작','Disney 골든 명작','아빠'),
('2026-09-20','인크레더블','한국어','창작','Disney Pixar · 골든 명작','아빠'),
('2026-09-21','내 이름은 더그','한국어','창작','Disney Pixar 업 · 골든 명작','아빠'),
('2026-09-21','정글의 왕 렉스','한국어','창작','Disney Pixar 토이 스토리 · 골든 명작','아빠'),
('2026-09-21','인사이드 아웃','한국어','창작','Disney Pixar · 골든 명작','아빠'),
('2026-09-21','소피아가 둘이야!','한국어','창작','Disney 리틀 프린세스 소피아 · 재독','아빠'),
]
for day,title,lang,genre,summary,companion in books:
    row=c.execute("SELECT id FROM riley_reading WHERE child='혜온' AND title=? AND read_date=? LIMIT 1",(title,day)).fetchone()
    if row:
        c.execute("UPDATE riley_reading SET language=?,genre=?,summary=?,companion=? WHERE id=?",(lang,genre,summary,companion,row['id']))
    else:
        c.execute("INSERT INTO riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child,companion) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(title,lang,genre,'','',day,0,summary,datetime.now().isoformat(timespec='seconds'),'혜온',companion))
c.commit(); c.close()
print('Hyeon reading Sep16-21 saved:',len(books))
