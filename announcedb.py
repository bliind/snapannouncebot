import aiosqlite
import uuid

database_file = 'announcebot.db'
async def sql_query(query, bind=()):
    try:
        async with aiosqlite.connect(database_file) as db:
            cursor = await db.execute(query, bind)
            if query.lower().startswith('select'):
                rows = await cursor.fetchall()
                await cursor.close()
                return rows
            else:
                await db.commit()
                return True
    except Exception as e:
        print('sql query failed:')
        print(e)
        print('query', query)
        print('bind', bind)
        return False

async def add_post(channel: str, content: str, link: str, datestamp: str):
    query = '''
        INSERT INTO posts
        (id, channel, content, link, datestamp)
        VALUES (?, ?, ?, ?, ?)
    '''
    bind = (str(uuid.uuid4()), channel, content, link, datestamp)

    return await sql_query(query, bind)

async def update_content(id, content):
    query = 'UPDATE posts SET content = ? WHERE id = ?'
    bind = (content, id)

    return await sql_query(query, bind)

async def get_last_posts():
    query = 'SELECT * FROM posts ORDER BY rowid DESC LIMIT 25'
    results = await sql_query(query)

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

async def get_support_message():
    query = 'SELECT message FROM support_message'
    results = await sql_query(query)
    return results[0][0]

async def update_support_message(new_message):
    query = 'UPDATE support_message SET message = ?'
    bind = (new_message,)

    return await sql_query(query, bind)
