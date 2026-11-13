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
    ('The Amazing Adventures of Ulysses','영어','고전','2026-09-25','3.7','620L'),
    ('환경 슈퍼히어로 태오 3: 위험에 처한 바다를 구하라!','한글','과학','2026-09-26','',''),
    ('환경 슈퍼히어로 태오 2: 암탉들을 구하라!','한글','과학','2026-09-26','',''),
    ('환경 슈퍼히어로 태오 1: 곤충들을 구하라!','한글','과학','2026-09-26','',''),
    ('어린이 과학동아 2025년 22호','한글','과학','2026-09-27','',''),
    ('어린이 과학동아 2025년 23호','한글','과학','2026-09-27','',''),
    ('어린이 과학동아 2025년 24호','한글','과학','2026-09-27','',''),
    ('A Comic Strip History of Planet Earth: Part 1 From the Big Bang to Birds','영어','과학','2026-09-27','',''),
    ('리틀 레이','한글','창작','2026-09-27','',''),
    ('미세먼지 수사대','한글','과학','2026-09-29','',''),
    ('The Story of Trains','영어','과학','2026-10-03','4.6','770L'),
    ('Macbeth','영어','고전','2026-10-03','3.6','480L'),
    ('오늘 식사, 세계일주를 만나다','한글','기타','2026-10-04','',''),
    ('열 살, 채근담을 만나다','한글','창작','2026-10-01','',''),
    ('열 살, 논어를 만나다','한글','창작','2026-10-01','',''),
    ('The Story of Cars','영어','과학','2026-10-02','4.6','800L'),
    ('The Revealing Story of Underwear','영어','역사','2026-10-02','5.4','860L'),
    ('정복왕 알렉산드로스','한글','역사','2026-10-02','',''),
    ('소년왕 투탕카멘','한글','역사','2026-10-03','',''),
    ('나는 천재가 아니야','한글','창작','2026-10-05','',''),
    ('게임 파티','한글','창작','2026-10-05','',''),
    ('조지, 마법의 약을 만들다','한글','창작','2026-10-05','',''),
    ('Bear Grylls Adventures: The Arctic Challenge','영어','창작','2026-10-05','3.8','590L'),
    ('빈둥빈둥 투닉스 왕','한글','창작','2026-10-06','',''),
    ('꿈을 향해 스타 오디션','한글','창작','2026-10-07','',''),
    ('또 한 번의 전학','한글','창작','2026-10-04','',''),
    ('동물 회의','한글','창작','2026-10-06','',''),
    ('Bear Grylls Adventures: The Sailing Challenge','영어','창작','2026-10-07','4.4','670L'),
    ('Bear Grylls Adventures: The Mountain Challenge','영어','창작','2026-10-09','4.2','620L'),
    ('안네의 일기','한글','역사','2026-10-09','',''),
    ('담배 피우는 엄마','한글','창작','2026-10-11','',''),
    ('제임스와 슈퍼 복숭아','한글','창작','2026-10-10','',''),
    ('열 살, 논어를 만나다','한글','창작','2026-10-11','',''),
    ('엄마 돌보기','한글','창작','2026-10-12','',''),
    ('The Story of Castles','영어','역사','2026-10-12','4.1','690L'),
    ('열 살, 맹자를 만나다','한글','인문','2026-10-13','',''),
    ('The Story of Ships','영어','역사','2026-10-13','','700L'),
    ('Bear Grylls Adventures: The Safari Challenge','영어','창작','2026-10-14','4.4','650L'),
    ('The Story of Football','영어','역사','2026-10-14','','840L'),
    ('Pinocchio','영어','고전','2026-10-15','3.8','640L'),
    ('Nelson','영어','역사','2026-10-15','','940L'),
    ('열 살, 목민심서를 만나다','한글','인문','2026-10-16','',''),
    ('Buried Alive: The Last Days of Pompeii','영어','역사','2026-10-16','',''),
    ('Winging It','영어','과학','2026-10-17','',''),
    ('William Shakespeare','영어','위인전','2026-10-17','','820L'),
    ('내 사촌은 천사 병동에 있다','한글','창작','2026-10-19','',''),
    ('해저 2만 리','한글','고전','2026-10-19','',''),
    ('톰 아저씨의 오두막','한글','고전','2026-10-20','',''),
    ('Nancy Drew and the Clue Crew #7: The Circus Scare','영어','창작','2026-10-22','3.7','580L'),
    ('푸른 사자 와니니 3: 새로운 약속','한글','창작','2026-10-26','',''),
    ('피와 혈액: 드라큘라도 궁금해!','한글','과학','2026-10-26','',''),
    ('로봇과 인공지능: 이젠 4차 산업 혁명!','한글','과학','2026-10-27','',''),
    ('랄프와 오토바이','한글','창작','2026-10-28','',''),
    ('미래 교통: 더 빨리, 더 멀리!','한글','과학','2026-10-29','',''),
    ('유럽','한글','지리','2026-10-30','',''),
    ('인생을 노래하는 로마의 후예','한글','역사','2026-10-31','',''),
    ('니콜라 테슬라','한글','위인전','2026-10-31','',''),
    ('제인 오스틴','한글','위인전','2026-11-01','',''),
    ('Stories of Vampires','영어','창작','2026-10-27','',''),
    ('Magic Animal Friends: Olivia Nibblesqueak\'s Messy Mischief','영어','창작','2026-10-29','',''),
    ('Magic Animal Friends: Rosie Gigglepip\'s Lucky Escape','영어','창작','2026-10-31','',''),
    ('떴다! 지식 탐험대 26: 출발, 공룡 멸종의 비밀을 찾아서!','한글','과학','2026-10-20','',''),
    ('Nancy Drew and the Clue Crew #9: The Halloween Hoax','영어','창작','2026-11-05','3.5','510L'),
    ('전쟁과 발명: 세상이 번쩍, 생각이 반짝!','한글','과학','2026-11-04','',''),
    ('북극의 눈물: 지구 끝에 무슨 일이?!','한글','과학','2026-11-06','',''),
    ('Bear Grylls Adventures: The Sailing Challenge','영어','창작','2026-11-07','4.4','670L'),
    ('Bear Grylls Adventures: The Sea Challenge','영어','창작','2026-11-13','4.4','670L'),
    ('The 39 Steps','영어','고전','2026-11-13','5.4','840L'),
    ('The Prisoner of Zenda','영어','고전','2026-11-13','4.0','600L'),
]


rcols={r['name'] for r in c.execute('PRAGMA table_info(riley_reading)').fetchall()}
for title,language,genre,read_date,sr_score,lexile_score in books:
    # Record each reading day separately; re-running this migration is idempotent.
    row=c.execute("SELECT id FROM riley_reading WHERE title=? AND COALESCE(read_date,'')=? LIMIT 1",(title,read_date)).fetchone()
    if not row:
        # Preserve undated legacy records by assigning their first known reading date.
        row=c.execute("SELECT id FROM riley_reading WHERE title=? AND COALESCE(read_date,'')='' LIMIT 1",(title,)).fetchone()
    if not row:
        fields=['title','language','rating','summary','created_at']
        values=[title,language,0,'',read_date+'T21:00:00']
        if 'genre' in rcols: fields.append('genre'); values.append(genre)
        if 'sr_score' in rcols: fields.append('sr_score'); values.append(sr_score)
        if 'lexile_score' in rcols: fields.append('lexile_score'); values.append(lexile_score)
        if 'read_date' in rcols: fields.append('read_date'); values.append(read_date)
        if 'child' in rcols: fields.append('child'); values.append('지유')
        q=','.join('?' for _ in fields)
        c.execute(f"INSERT INTO riley_reading({','.join(fields)}) VALUES({q})",values)
    else:
        updates=[]; vals=[]
        if 'child' in rcols:
            updates.append("child=CASE WHEN COALESCE(child,'')='' THEN '지유' ELSE child END")
        if 'read_date' in rcols:
            updates.append("read_date=CASE WHEN COALESCE(read_date,'')='' THEN ? ELSE read_date END"); vals.append(read_date)
        if 'sr_score' in rcols and sr_score:
            updates.append("sr_score=?"); vals.append(sr_score)
        if 'lexile_score' in rcols and lexile_score:
            updates.append("lexile_score=?"); vals.append(lexile_score)
        if updates:
            vals.append(row['id']); c.execute('UPDATE riley_reading SET '+','.join(updates)+' WHERE id=?',vals)

confirmed_dates={'The Worst Witch':'2026-06-22'}
for title,read_date in confirmed_dates.items():
    c.execute("UPDATE riley_reading SET read_date=? WHERE title=? AND COALESCE(read_date,'')=''",(read_date,title))

c.commit(); c.close()
print('Riley reading dates and levels migrated')
