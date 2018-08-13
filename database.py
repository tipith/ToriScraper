import logging
import MySQLdb
import MySQLdb.cursors
import traceback

import config


db_logger = logging.getLogger('database')


class DBConnection:
    def __init__(self, connect_with_name=True):
        self.db = None
        self.connect_with_name = connect_with_name

    def __enter__(self):
        if self.connect_with_name:
            self.db = MySQLdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pass, db=config.db_name,
                                      cursorclass=MySQLdb.cursors.DictCursor)
        else:
            self.db = MySQLdb.connect(host=config.db_host, user=config.db_user, passwd=config.db_pass,
                                      cursorclass=MySQLdb.cursors.DictCursor)
        return self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()


def _execute(sql, vals=None, with_name=True, fetch=False):
    with DBConnection(with_name) as cur:
        try:
            cur.execute(sql, vals)
            if fetch:
                return cur.fetchall()
        except Exception:
            db_logger.error(cur._last_executed)
            db_logger.error(traceback.format_exc())


sql_create_alarm = '''
CREATE TABLE `Alarm` (
  `AlarmId` int(11) NOT NULL AUTO_INCREMENT,
  `SearchPattern` varchar(100) CHARACTER SET latin1 DEFAULT NULL,
  `MaxPrice` int(11) DEFAULT NULL,
  `MinPrice` int(11) DEFAULT NULL,
  `UserId` int(11) DEFAULT NULL,
  `Location` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`AlarmId`),
  KEY `fk_alarm_user_idx` (`UserId`),
  CONSTRAINT `fk_alarm_user` FOREIGN KEY (`UserId`) REFERENCES `User` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
'''

sql_create_item = '''
CREATE TABLE `Item` (
  `ItemId` int(11) NOT NULL AUTO_INCREMENT,
  `Description` varchar(200) CHARACTER SET latin1 DEFAULT NULL,
  `Price` int(11) DEFAULT NULL,
  `Date` datetime DEFAULT NULL,
  `ImageURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriId` int(11) DEFAULT NULL,
  `Category` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `Location` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`ItemId`)
) ENGINE=InnoDB AUTO_INCREMENT=1434112 DEFAULT CHARSET=utf8;
'''

sql_create_itemalarm = '''
CREATE TABLE `ItemAlarm` (
  `ItemAlarmId` int(11) NOT NULL AUTO_INCREMENT,
  `Description` varchar(200) CHARACTER SET latin1 DEFAULT NULL,
  `Price` int(11) DEFAULT NULL,
  `Date` datetime DEFAULT NULL,
  `ImageURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriURL` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `ToriId` int(11) DEFAULT NULL,
  `Category` varchar(145) CHARACTER SET latin1 DEFAULT NULL,
  `Location` varchar(45) CHARACTER SET latin1 DEFAULT NULL,
  `UserId` int(11) DEFAULT NULL,
  PRIMARY KEY (`ItemAlarmId`),
  KEY `fk_itemalarm_user_idx` (`UserId`),
  CONSTRAINT `fk_itemalarm_user` FOREIGN KEY (`UserId`) REFERENCES `User` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=2070 DEFAULT CHARSET=utf8;
'''

sql_create_user = '''CREATE TABLE `User` (
  `UserId` int(11) NOT NULL AUTO_INCREMENT,
  `Email` varchar(100) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`UserId`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
'''

def create_if_needed():
        rows = _execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (config.db_name,),
                        with_name=False,
                        fetch=True)
        if not rows:
            db_logger.warning('database was not found, creating it')
            _execute("CREATE DATABASE `{}` /*!40100 DEFAULT CHARACTER SET utf8 */;".format(config.db_name), with_name=False)
            _execute(sql_create_item)
            _execute(sql_create_user)
            _execute(sql_create_alarm)
            _execute(sql_create_itemalarm)


def get_alarms():
    return _execute("SELECT * FROM Alarm", fetch=True)


def get_email(user_id):
    rows = _execute("SELECT * FROM User WHERE UserId = %s", [user_id], fetch=True)
    return rows[0]['Email']


def get_items(date, category=None):
    start = date.strftime("%Y-%m-%d")
    end = date.strftime("%Y-%m-%d 23:59:59")
    rows = _execute("SELECT * FROM Item WHERE Date BETWEEN %s AND %s", (start, end), fetch=True)
    return list(rows)


def get_descriptions():
    rows = _execute("SELECT Description FROM Item", fetch=True)
    return list(rows)


def store_item_alarm(user_id, item):
    _execute("INSERT INTO ItemAlarm (Description, Price, Date, ImageURL, ToriURL, ToriId, Category, Location, UserId) \
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
             (item['description'], item['price'], item['date'], item['image_url'], item['tori_url'],
              item['id'], item['category'], item['location'], user_id))


def store_items(items):
    with DBConnection() as cursor:
        try:
            items_list = [(item['description'], item['price'], item['date'], item['image_url'], item['tori_url'], item['id'],
                           item['category'], item['location']) for item in items]
            cursor.executemany("INSERT INTO Item (Description, Price, Date, ImageURL, ToriURL, ToriId, Category, Location) \
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", items_list)
        except (MySQLdb.IntegrityError, UnicodeEncodeError):
            db_logger.warning('unable to add entries')
            db_logger.warning(traceback.format_exc())


if __name__ == '__main__':
    import datetime
    for alarm in get_alarms():
        print("%s -> %s" % (alarm, get_email(alarm['UserId'])))
    test_item = {'id': 1234, 'description': 'testcription äöäöåå', 'location': 'testland', 'buy_or_sell': 'Myydään',
                 'price': 'n/a', 'date': datetime.datetime.now(), 'image_url': None, 'tori_url': 'https://jee',
                 'category': 'testigory'}
    store_item_alarm(1, test_item)
