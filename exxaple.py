import sqlite3 as sql

db = sql.connect('db/database.db')
cursor = db.cursor()
cursor.execute('''
    create table if not exists score(
        score_id integer primary key autoincrement,
        value integer
    );
''')

cursor.execute('''select value from score''')
score = cursor.fetchone()
if not score:
    cursor.execute('''
        insert into score (value) values (?);
    ''', (0,))
cursor.execute('''select value from score''')
score = cursor.fetchone()[0]

db.commit()
db.close()










