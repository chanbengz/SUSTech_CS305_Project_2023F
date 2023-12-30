from sqlite3 import *

def register(user, passwd):
    con = connect('Database/users.db')
    cur = con.cursor()
    cur.execute(f"insert into users values('{user}', '{passwd}')")
    con.commit()
    con.close()

if __name__ == '__main__':
    register(input('Username: '), input('Password: '))