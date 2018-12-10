import logging
import MySQLdb
import MySQLdb.cursors
import traceback
import glob
import pathlib

import config


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
        self.db.set_character_set('utf8')
        return self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()


class DummyDBConnection:
    def __init__(self, connect_with_name=True):
        pass

    def __enter__(self):
        class DummyCursor:
            def execute(self, sql, vals):
                pass
            def executemany(self, sql, vals):
                pass
            def fetchall(self):
                return []
        return DummyCursor()

    def __exit__(self, type, value, traceback):
        pass


class ToriSQLDB:

    def __init__(self, dbconn):
        self.db = dbconn
        self.logger = logging.getLogger(self.__class__.__name__)
        self._create_if_needed()

    def _execute(self, sql, vals=None, with_name=True, fetch=False):
        with self.db(with_name) as cur:
            try:
                cur.execute(sql, vals)
                if fetch:
                    return cur.fetchall()
            except Exception:
                self.logger.error(cur._last_executed)
                self.logger.error(traceback.format_exc())

    def _create_if_needed(self):
        rows = self._execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (config.db_name,),
                        with_name=False,
                        fetch=True)
        if not rows:
            self.logger.warning('database {} was not found, creating it'.format(config.db_name))
            self._execute("CREATE DATABASE `{}` /*!40100 DEFAULT CHARACTER SET utf8 */;".format(config.db_name), with_name=False)
        for file_name in glob.glob(str(pathlib.Path('dbscripts', '*_table_*.sql'))):
            table_name = file_name.split('_')[-1].split('.')[0]
            if not self._execute('SHOW TABLES LIKE %s', (table_name,), fetch=True):
                self.logger.warning('table {} was not found, creating it'.format(table_name))
                with open(file_name, mode='r') as f:
                    self._execute(f.read())

    def add_user(self, email):
        return self._execute("INSERT INTO User (Email) Values (%s)", (email,))

    def get_alarms(self):
        return self._execute("SELECT * FROM Alarm", fetch=True)

    def get_email(self, user_id):
        rows = self._execute("SELECT * FROM User WHERE UserId = %s", [user_id], fetch=True)
        return rows[0]['Email']

    def get_items(self, date=None, category=None):
        if date:
            start = date.strftime("%Y-%m-%d")
            end = date.strftime("%Y-%m-%d 23:59:59")
            rows = self._execute("SELECT * FROM Item WHERE Date BETWEEN %s AND %s", (start, end), fetch=True)
        else:
            rows = self._execute("SELECT * FROM Item ORDER BY ItemId DESC LIMIT 100000", fetch=True)
        return list(rows)

    def get_descriptions(self):
        rows = self._execute("SELECT Description FROM Item", fetch=True)
        return list(rows)

    def store_item_alarm(self, user_id, item):
        self._execute("INSERT INTO ItemAlarm (Description, Price, Date, ImageURL, ToriURL, ToriId, Category, Location, UserId) \
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                      (item.description, item.price, item.date, item.imageurl, item.toriurl,
                       item.toriid, item.category, item.location, user_id))

    def store_items(self, items):
        with self.db() as cur:
            try:
                items_list = [(item.description, item.price, item.date, item.imageurl, item.toriurl, item.toriid,
                               item.category, item.location) for item in items]
                cur.executemany("INSERT INTO Item (Description, Price, Date, ImageURL, ToriURL, ToriId, Category, Location) \
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", items_list)
            except (MySQLdb.IntegrityError, UnicodeEncodeError):
                self.logger.warning('unable to add entries')
                self.logger.warning(traceback.format_exc())

    def get_cars(self):
        rows = self._execute('SELECT * FROM Car ORDER BY ItemId DESC LIMIT 10000', fetch=True)
        return list(rows)

    def store_cars(self, items):
        with self.db() as cur:
            items_list = [(i.description, i.price, i.date, i.imageurl, i.toriurl,
                           i.toriid, i.category, i.location, i.car_ac, i.car_cruise,
                           i.car_engine_heater, i.car_hook, i.car_fuel_expense, i.car_tax, i.car_year,
                           i.car_odo, i.car_fuel_type, i.car_gear, i.car_plate, i.car_type,
                           i.car_description_extra, i.car_info) for i in items]
            try:
                cur.executemany("INSERT INTO Car ("
                                "Description, Price, Date, ImageURL, ToriURL, "
                                "ToriId, Category, Location, car_ac, car_cruise, "
                                "car_engine_heater, car_hook, car_fuel_expense, car_tax, car_year, "
                                "car_odo, car_fuel_type, car_gear, car_plate, car_type, "
                                "car_description_extra, car_info) "
                                "VALUES ("
                                "%s, %s, %s, %s, %s, "
                                "%s, %s, %s, %s, %s, "
                                "%s, %s, %s, %s, %s, "
                                "%s, %s, %s, %s, %s, "
                                "%s, %s)", items_list)
            except:
                self.logger.error(cur._last_executed)
                self.logger.warning('unable to add entries')
                self.logger.warning(traceback.format_exc())

class DBFactory:

    @staticmethod
    def create():
        if 'dummy' in config.db_conn.lower():
            return ToriSQLDB(DummyDBConnection)
        return ToriSQLDB(DBConnection)


if __name__ == '__main__':
    import datetime
    db = ToriSQLDB(DBConnection)
    db.add_user('testuser@test.com')
    for alarm in db.get_alarms():
        print("%s -> %s" % (alarm, db.get_email(alarm['UserId'])))
    test_item = {'id': 1234, 'description': 'testcription äöäöåå', 'location': 'testland', 'buy_or_sell': 'Myydään',
                 'price': 3, 'date': datetime.datetime.now(), 'imageurl': None, 'toriurl': 'https://jee',
                 'category': 'testigory'}
    db.store_item_alarm(2, test_item)
