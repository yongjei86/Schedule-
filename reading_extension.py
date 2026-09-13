import os
import secrets
from datetime import datetime
from flask import jsonify, request

SEED_BOOKS = [
    {'child':'혜온','title':'Rapunzel Can','language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':'Family','language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':"Belle's Wedding Day",'language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':'What Is a Friend?','language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':"Belle's Tea Party",'language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':'Safe!','language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':'In the Castle','language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':"Cinderella's Wedding",'language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
    {'child':'혜온','title':'The Snowy Day','language':'영어','genre':'영어 원서','read_date':'2026-09-13','rating':0,'summary':'Disney Reading Adventures Level 1'},
]


def normalize_book(raw):
    title = str(raw.get('title') or '').strip()
    if not title:
        raise ValueError('title is required')
    child = str(raw.get('child') or '혜온').strip()
    if child not in ('지유','혜온'):
        raise ValueError('child must be 지유 or 혜온')
    try:
        rating = max(0,min(5,int(raw.get('rating') or 0)))
    except (TypeError,ValueError):
        rating = 0
    return {
        'title':title,'child':child,
        'language':str(raw.get('language') or '').strip(),
        'genre':str(raw.get('genre') or '').strip(),
        'sr_score':str(raw.get('sr_score') or '').strip(),
        'lexile_score':str(raw.get('lexile_score') or '').strip(),
        'read_date':str(raw.get('read_date') or '').strip(),
        'rating':rating,
        'summary':str(raw.get('summary') or '').strip(),
    }


def insert_book(db, book):
    c=db()
    try:
        exists=c.execute('select id from riley_reading where child=? and title=? and read_date=? limit 1',(book['child'],book['title'],book['read_date'])).fetchone()
        if exists:
            return int(exists['id']),False
        cur=c.execute('insert into riley_reading(title,language,genre,sr_score,lexile_score,read_date,rating,summary,created_at,child) values(?,?,?,?,?,?,?,?,?,?)',(book['title'],book['language'],book['genre'],book['sr_score'],book['lexile_score'],book['read_date'],book['rating'],book['summary'],datetime.now().isoformat(timespec='seconds'),book['child']))
        c.commit()
        return int(cur.lastrowid),True
    finally:
        c.close()


def register(app, db):
    added=0
    skipped=0
    for raw in SEED_BOOKS:
        try:
            _,created=insert_book(db,normalize_book(raw))
            added+=int(created); skipped+=int(not created)
        except Exception as e:
            print(f'Reading seed skipped: {e}',flush=True)
    print(f'Hyeon reading seed: added={added}, skipped={skipped}',flush=True)

    @app.post('/api/reading/add')
    def api_reading_add():
        expected=os.getenv('READING_API_KEY','')
        supplied=request.headers.get('X-API-Key','')
        if not expected or not secrets.compare_digest(supplied,expected):
            return jsonify({'ok':False,'error':'unauthorized'}),401
        payload=request.get_json(silent=True) or {}
        rows=payload.get('books') if isinstance(payload,dict) and 'books' in payload else [payload]
        if not isinstance(rows,list) or not rows:
            return jsonify({'ok':False,'error':'books must be a non-empty list'}),400
        out=[]
        try:
            for raw in rows:
                book=normalize_book(raw)
                book_id,created=insert_book(db,book)
                out.append({'id':book_id,'title':book['title'],'child':book['child'],'created':created})
        except ValueError as e:
            return jsonify({'ok':False,'error':str(e)}),400
        except Exception:
            return jsonify({'ok':False,'error':'database error'}),500
        return jsonify({'ok':True,'results':out})
