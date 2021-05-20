

import psycopg2
def saveDB(msg):
    try:
        #conn = psycopg2.connect(host='54.180.113.136', dbname='cssdb', user='postgres', password='1234', port='5432') # db에 접속
        conn = psycopg2.connect("host=13.124.19.47 dbname=testdb user=testuser password=testuser1! port=5432")
        # autocommit 없으면, InternalError: CREATE DATABASE cannot run inside a transaction block
    except psycopg2.Error as e:
        print('Failt to connection Error')
        print(e)
        if conn:
            conn.rollback()
    else:
        conn.autocommit = True
        rows = None
        cur = conn.cursor()
        #cur.execute("INSERT INTO room_info VALUES(default,'123EQQ345', NULL,NULL)")
        if len(msg) < 1:
            for strline in msg:
                cur.execute(strline)
        else:
            rows = cur.execute(msg)

        #cur.execute("INSERT INTO room_info VALUES(default,'134RKGI13', NULL,NULL)")
        #cur.execute("INSERT INTO room_info VALUES(default,'GG36728EE', NULL,NULL)")
        #cur.execute("INSERT INTO room_info VALUES(default,'145XER111', NULL,NULL)")
        #cur.execute("update room_info set user_name = '천상욱', room_code = '81SP236H' where licencekey = '123EQQ345'")
        #cur.execute("SELECT * FROM sometable")
        #cur.execute("SELECT id, name FROM sometable WHERE value1=%s AND value2=%s",
        #               (value1, value2))
        # table 만들기
        #cur.execute("CREATE TABLE Cars(Id INTEGER PRIMARY KEY, Name VARCHAR(20), Price INT)") # data insert
        #cur.execute("INSERT INTO Cars VALUES(1,'Audi',52642)")
        #cur.execute("INSERT INTO Cars VALUES(2,'Mercedes',57127)")
        #cur.execute("SELECT * FROM Cars")
        #rows = None
        if msg[:6] == 'SELECT' or msg[:6] == 'select':
            rows = cur.fetchall()

        conn.commit()
        # 출처: https://freeprog.tistory.com/100 [취미로 하는 프로그래밍 !!!]

        if conn:
            conn.close()
        return rows