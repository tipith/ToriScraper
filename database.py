import logging
import MySQLdb
import MySQLdb.cursors
import traceback

import config


db_logger = logging.getLogger('database')


class DBConnection:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = MySQLdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pass, db="ToriScraper",
                                  cursorclass=MySQLdb.cursors.DictCursor)
        return self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()


def get_alarms():
    with DBConnection() as cursor:
        cursor.execute("SELECT * FROM Alarm")
        rows = cursor.fetchall()
    return rows


def get_email(user_id):
    with DBConnection() as cursor:
        cursor.execute("SELECT * FROM User WHERE UserId = %s", [user_id])
        rows = cursor.fetchall()
    return rows[0]['Email']


def store_item_alarm(user_id, item):
    with DBConnection() as cursor:
        try:
            cursor.execute("INSERT INTO ItemAlarm (Description, Price, Date, ImageURL, ToriURL, ToriId, Category, Location, UserId) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (item['description'], item['price'], item['date'], item['image_url'], item['tori_url'],
                            item['id'], item['category'], item['location'], user_id))
        except MySQLdb.IntegrityError:
            db_logger.warning('unable to add entry')
            db_logger.warning(traceback.format_exc())


if __name__ == '__main__':
    import datetime
    for alarm in get_alarms():
        print("%s -> %s" % (alarm, get_email(alarm['UserId'])))
    test_item = {'id': 1234, 'description': 'testcription äöäöåå', 'location': 'testland', 'buy_or_sell': 'Myydään',
                 'price': 'n/a', 'date': datetime.datetime.now(), 'image_url': None, 'tori_url': 'https://jee',
                 'category': 'testigory'}
    store_item_alarm(1, test_item)
