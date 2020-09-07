import psycopg2
import pdb
import datetime
import os

def checkupdate(vals):
    connection = None

    now = str(datetime.datetime.now())
    new = now + " something"

    try:
        connection = psycopg2.connect(
            database=vals['database'],
            user=vals['user'],
            password=vals['password'],
            host=vals['host'],
            port=vals['port']
        )

        f = open('demo.txt', 'a')

        log = now + " connected success\n"
        f.write(log)
        f.close()
    except Exception as e:
        # print(vals['db_name'], vals['db_user_name'], )
        print(e)



    finally:
        if connection:
            cursor = connection.cursor()
            check_table = '''select count(*) from information_schema.tables where table_schema = 'public';'''
            cursor.execute(check_table)
            list_tables = cursor.fetchall()

            if(list_tables==[(0,)]):


                f = open('demo.txt', 'a')
                log = now + " empty\n"
                f.write(log)
                f.close()
                connection.close()
                return True
            else:

                f = open('demo.txt', 'a')
                log = now + " data is there\n"
                f.write(log)
                f.close()
                connection.close()
                return False

vals = {
                'database':'test3',
                'user':'powerbiuser',
                'password':'powerbipassword',
                'host':'powerbidemos.cou0prdetmzo.ap-south-1.rds.amazonaws.com',
                'port':5432
        }
def showlogs():

    path = './demo.txt'
    n = 50
    fd = os.open(path, os.O_RDWR)
    s = "GeeksForGeeks: A Computer science portal for Geeks."
    s2 = 'ss'
    line = str.encode(s2)
    numBytes = os.write(fd, line)
    print("Number of bytes written:", numBytes)
    os.close(fd)
    # logFile = os.open(path, os.O_RDONLY)
    # readBytes = os.read(logFile,n)
    # print(readBytes)
    # os.close()
status = checkupdate(vals)
showlogs()

import datetime

# obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', args[0][0])])

now = str(datetime.datetime.now())
f = open('demo.txt','r')
obj = f.read()
f.close()
old_log = obj
f = open('demo.txt','w')

obj = now + ' something \n' + old_log
f.write(obj)
f.close()
