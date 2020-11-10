import pymysql


def create_mysql_conn():
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', port=13306, db='mdbmp')
    cur = db.cursor(cursor=pymysql.cursors.DictCursor)
    return db, cur


if __name__ == '__main__':
    pass
