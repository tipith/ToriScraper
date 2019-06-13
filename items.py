import datetime, logging, re, inspect, hashlib
import gmail


class ToriItem:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k.translate('-').lower(), v)
        if not isinstance(self.date, datetime.datetime):
            self.date = ToriItem._convert_date(self.date)
        self.hash = hash((self.toriid, self.price))

    def __hash__(self):
        return self.hash

    def __str__(self):
        return '{0} - {1} {2: >30} {3: >10} {4: <45} {5}'.format(
            self.toriid, self.date.strftime("%Y-%m-%d %H:%M"), self.location, str(self.price), self.description, self.toriurl)

    def add(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    @staticmethod
    def _convert_date(d):
        # modify strings representing dates to python datetimes
        months_fin = {1: 'tam', 2: 'hel', 3: 'maa', 4: 'huh', 5: 'tou', 6: 'kes',
                      7: 'hei', 8: 'elo', 9: 'syy', 10: 'lok', 11: 'mar', 12: 'jou'}
        months_fin2en = {'tam': 'Jan', 'hel': 'Feb', 'maa': 'Mar', 'huh': 'Apr', 'tou': 'May', 'kes': 'Jun',
                         'hei': 'Jul', 'elo': 'Aug', 'syy': 'Sep', 'lok': 'Oct', 'mar': 'Nov', 'jou': 'Dec'}
        today = datetime.date.today()
        yesterday = datetime.date.today() - datetime.timedelta(1)

        if 'tänään' in d:
            d = '{} {} {}'.format(today.day, months_fin[today.month], d.split()[1])
        if 'eilen' in d:
            d = '{} {} {}'.format(yesterday.day, months_fin[yesterday.month], d.split()[1])
        # all dates are now in format 'DD Month HH:MM'
        date_split = d.split()
        d = '{} {} {}'.format(date_split[0], months_fin2en[date_split[1]], date_split[2])
        d = datetime.datetime.strptime(d, '%d %b %H:%M').replace(year=today.year)
        return d


class ToriItemList:

    def __init__(self, name, db=None, populate=False):
        self.name = name
        self.logger = logging.getLogger(name + '_list')
        self.items = []
        self.db = db
        if populate:
            self.populate()

    @classmethod
    def create_from_another_list(cls, other):
        l = cls(other.name, other.db)
        l.items = other.items.copy()
        return l

    def __add__(self, other):
        self.items += other.items
        return self

    def __str__(self):
        return '\n'.join([str(item) for item in self.items])

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key) -> ToriItem:
        if len(self.items) == 0:
            return None
        return self.items[key]

    def __iter__(self):
        self.item_num = 0
        return self

    def __next__(self) -> ToriItem:
        if self.item_num >= len(self.items):
            raise StopIteration
        else:
            item = self.items[self.item_num]
            self.item_num += 1
            return item

    def replace_items(self, items):
        self.items = [i for i in items if isinstance(i, ToriItem)]

    def findById(self, id) -> ToriItem:
        for i in self.items:
            if i.toriid == id:
                return i

    def add(self, item: ToriItem):
        self.items.append(item)

    def diff_to(self, other):
        my_hashes = [hash(item) for item in self.items]
        rv = self.__class__('diff')
        rv.items = [item for item in other.items if hash(item) not in my_hashes]
        return rv

    def reset(self):
        self.items = []

    def remove_buys(self):
        self.items = list(filter(lambda item: item.buy_or_sell == 'Myydään', self.items))

    def sort_by_date(self):
        return sorted(self.items, reverse=False, key=lambda k: k.date)

    def truncate_oldest(self, n):
        self.sort_by_date()
        if len(self.items) > n:
            self.logger.info('removing {} oldest items'.format(len(self.items) - n))
            self.items = self.items[-n:]

    def populate(self):
        if self.db:
            fetched = self.db.get_items()
            self.items = [ToriItem(**x) for x in fetched]

    def persist(self):
        if self.db and len(self.items):
            self.db.store_items(self.items)

    def check_for_alarms(self):
        if not self.db or not len(self.items):
            return
        alarms = self.db.get_alarms()
        if not alarms:
            return
        alarms_sent = {}

        for alarm in alarms:
            if 'SearchPattern' in alarm and alarm['SearchPattern']:
                alarm['RegexSearchPattern'] = re.compile(alarm['SearchPattern'], re.IGNORECASE)
            if 'Location' in alarm and alarm['Location']:
                alarm['RegexLocation'] = re.compile(alarm['Location'], re.IGNORECASE)

        self.logger.debug('alarms: {}'.format(alarms))
        for item in self.items:
            for alarm in alarms:
                description_ok = False if 'SearchPattern' in alarm and alarm['SearchPattern'] else True
                location_ok = False if 'Location' in alarm and alarm['Location'] else True
                maxprice_ok = False if 'MaxPrice' in alarm and alarm['MaxPrice'] else True
                minprice_ok = False if 'MinPrice' in alarm and alarm['MinPrice'] else True

                if 'SearchPattern' in alarm and alarm['SearchPattern']:
                    if alarm['RegexSearchPattern'].match(item.description):
                        description_ok = True

                if description_ok and 'Location' in alarm and alarm['Location']:
                    if alarm['RegexLocation'].match(item.location):
                        location_ok = True

                if description_ok and location_ok and isinstance(item.price, int):
                    if 'MaxPrice' in alarm and alarm['MaxPrice'] and item.price < alarm['MaxPrice']:
                        maxprice_ok = True
                    if 'MinPrice' in alarm and alarm['MinPrice'] and item.price > alarm['MinPrice']:
                        minprice_ok = True

                self.logger.debug('description {0: <20} {1: <20} item value {2: <20}'.format(
                    alarm['SearchPattern'] if alarm['SearchPattern'] else 'None',
                    'passed' if description_ok else 'failed',
                    item.description))
                self.logger.debug('location    {0: <20} {1: <20} item value {2: <20}'.format(
                    alarm['Location'] if alarm['Location'] else 'None',
                    'passed' if location_ok else 'failed',
                    item.location))
                self.logger.debug('maxprice    {0: <20} {1: <20} item value {2: <20}'.format(
                    alarm['MaxPrice'] if alarm['MaxPrice'] else 'None',
                    'passed' if maxprice_ok else 'failed',
                    item.price if item.price else 'None'))
                self.logger.debug('minprice    {0: <20} {1: <20} item value {2: <20}'.format(
                    alarm['MinPrice'] if alarm['MinPrice'] else 'None',
                    'passed' if maxprice_ok else 'failed',
                    item.price if item.price else 'None'))

                if all([description_ok, location_ok, maxprice_ok, minprice_ok]):
                    if item.toriid not in alarms_sent or (
                            item.toriid in alarms_sent and alarm['UserId'] not in alarms_sent[item.toriid]):
                        email = self.db.get_email(alarm['UserId'])
                        if email:
                            self.logger.info(
                                'alarm {} for "{}, {} eur"'.format(email, item.description, item.price))
                            gmail.send(email, 'Tori.fi: {}, {}'.format(item.description, item.price),
                                       item.toriurl, None)
                            self.db.store_item_alarm(alarm['UserId'], item)
                        else:
                            self.logger.info('alarm found "{}, {} eur"'.format(item.description, item.price))
                        alarms_sent.setdefault(item.toriid, []).append(alarm['UserId'])
                    else:
                        self.logger.info('alarm already sent to UserId {} for "{}, {} eur"'.format(alarm['UserId'],
                                                                                                   item.description,
                                                                                                   item.price))

class CarItemList(ToriItemList):

    def populate(self):
        if self.db:
            self.items = [ToriItem(**x) for x in self.db.get_cars()]

    def persist(self):
        if self.db:
            self.db.store_cars(self.items)