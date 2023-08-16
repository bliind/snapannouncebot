import sqlite3
import uuid

def open_db():
    return sqlite3.connect('announcebot.db')

def add_post(channel: str, content: str, link: str, datestamp: str):
    try:
        conn = open_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO posts (id, channel, content, link, datestamp) VALUES (?, ?, ?, ?, ?)', (str(uuid.uuid4()), channel, content, link, datestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print('Failed to add post:')
        print(e)
        return False

def update_content(rowid, content):
    try:
        conn = open_db()
        cur = conn.cursor()
        cur.execute('UPDATE posts SET content = ? WHERE rowid = ?', (content, rowid))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print('Failed to update post:')
        print(e)
        return False

def get_last_posts():
    conn = open_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM posts ORDER BY rowid DESC LIMIT 5')
    results = cur.fetchall()
    conn.close()

    out = []
    if results:
        for result in results:
            out.append({
                "id":        result[0],
                "channel":   result[1],
                "content":   result[2],
                "link":      result[3],
                "datestamp": result[4],
            })

    return out
