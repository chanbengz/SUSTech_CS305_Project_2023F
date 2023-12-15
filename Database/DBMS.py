from sqlite3 import *

def clear_cookies():
    con = connect('Database/cookies.db')
    con.execute("DELETE FROM cookies")
    con.commit()
    con.close()

def get_cookies():
    con = connect('Database/cookies.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM cookies")
    for row in cur:
        print(row[0], row[1], row[2])

if __name__ == '__main__':
    get_cookies()
    clear_cookies()