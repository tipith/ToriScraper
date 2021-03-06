from bs4 import BeautifulSoup
import urllib.request, urllib.error, urllib.parse
import re, traceback, logging, datetime, functools
import multiprocessing.dummy as mp

from items import ToriItemList, CarItemList, ToriItem


class ToriParser:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.topic = ''

    @staticmethod
    def _get_number(text):
        if not text:
            return None
        no_ws = ''.join(text.split())
        matches = re.findall(r'\d+', no_ws)
        return int(matches[0]) if matches else None

    def _category_parser(self, soup):
        if soup is not None:
            titles = soup['title'].split(',')
            titles = list(map(str.strip, titles))
            city = titles[-2]
            category = titles[-3]
            return city, category
        return None, None

    def list_factory(self, *args, **kwargs) -> ToriItemList:
        return ToriItemList(*args, **kwargs)

    def parse(self, html) -> ToriItemList:
        if not html:
            return ToriItemList('fail')
        soup = BeautifulSoup(html, 'html.parser')
        discarded = re.compile(r'(prisjakt|pp_item|listing_carousel)')
        accepted = re.compile(r'^item_\d+$')

        rows = soup.body.find_all('a', class_='item_row')
        items = ToriItemList('fetch')
        items_total = 0

        for row in rows:
            try:
                if 'id' not in row.attrs:
                    continue

                if not discarded.match(row.attrs['id']) and accepted.match(row.attrs['id']):
                    items_total += 1

                has_image = row.find('div', class_='sprite_list_no_image') is None
                numerals = [int(s) for s in row['id'].split('_') if s.isdigit()]
                if not numerals:
                    continue
                date_raw = row.find('div', class_='date_image').text.strip()
                date_processed = re.sub(r'[\t]', '', date_raw)
                date_processed = re.sub(r'[\n]', ' ', date_processed)
                item = {
                    'toriid': numerals[0],
                    'description': row.find('div', class_='li-title').text,
                    'price': row.find('p', class_='list_price').text,
                    'date': date_processed,
                    'imageurl': row.find('img', class_='item_image')['src'] if has_image else None,
                    'toriurl': row['href']
                }
                
                city, category = self._category_parser(row.find('img', class_='item_image'))
                cat_geo = row.find('div', class_='cat_geo')
                item['location'] = cat_geo.find_all('p')[0].text.strip() + (', ' + city) if city else ''
                item['buy_or_sell'] = cat_geo.find_all('p')[1].text.strip()
                item['category'] = category

                try:
                    item['price'] = ToriParser._get_number(item['price'])
                except IndexError:
                    self.logger.debug('unknown price format: {0}'.format(item['price']))
                    item['price'] = None

                    self.logger.debug('parsed:\n{}\n{}\n\n'.format('-' * 70, row.prettify()))
                items.add(ToriItem(**item))
            except KeyboardInterrupt as e:
                raise e
            except:
                self.logger.error('Unable to parse:\n{}\n{}\n\n'.format('-' * 70, row.prettify()))
                self.logger.error('Exception:\n{}'.format(traceback.format_exc()))
        self.logger.debug('successfully parsed {0}/{1}'.format(len(items), items_total))
        return items

    def enrich(self, url_getter, item: ToriItem):
        return item  # return unmodified


class CarParser(ToriParser):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.topic = '/autot'

    def list_factory(self, *args, **kwargs) -> CarItemList:
        return CarItemList(*args, **kwargs)

    def parse(self, html) -> CarItemList:
        return CarItemList.create_from_another_list(super().parse(html))

    def enrich(self, url_getter, item: ToriItem):
        html = url_getter(item.toriurl, user_msg=str(item.date))
        if not html:
            return None
        soup = BeautifulSoup(html, 'html.parser')
        det_fin = {}
        for row in soup('td', class_='topic'):
            if row.next_sibling.next_sibling:
                det_fin[row.text.strip(':')] = row.next_sibling.next_sibling.text.strip()
        #print(det_fin)
        det = {}
        det['car_type'] = det_fin.get('Ajoneuvotyyppi', None)
        det['car_year'] = ToriParser._get_number(det_fin.get('Vuosimalli', None))
        det['car_tax'] = ToriParser._get_number(det_fin.get('Ajoneuvovero', None))
        det['car_odo'] = ToriParser._get_number(det_fin.get('Mittarilukema', None))
        det['car_fuel_expense'] = ToriParser._get_number(det_fin.get('Polttoainekulut', None))
        det['car_gear'] = det_fin.get('Vaihteisto', None)
        det['car_fuel_type'] = det_fin.get('Polttoaine', None)
        det['car_plate'] = det_fin.get('Rekisterinumero', None)
        det['car_cruise'] = det_fin.get('Vakionopeudensäädin', None) != '-'
        det['car_hook'] = det_fin.get('Vetokoukku', None) != '-'
        det['car_ac'] = det_fin.get('Ilmastointi', None) != '-'
        det['car_engine_heater'] = det_fin.get('Lohkolämmitin', None) != '-'
        img = soup('img', class_='image_next')
        det['imageurl'] = img[0]['src'] if img else None
        sub = soup('div', class_='sub_subject')
        sub_topic = sub[0]('div', class_='ad_param') if sub else None
        det['car_description_extra'] = sub_topic[0].text if sub_topic else None
        det['car_info'] = soup('div', class_='body')[0].text.strip('\n').strip()
        det['car_info'] = ' '.join([line.strip() for line in det['car_info'].split('\n')])
        item.add(**det)
        return item


class ToriConsumer:

    def __init__(self, parser, max_pages):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parser = parser
        self.pages_max = max_pages
        self.pages_at_once = max(self.pages_max // 10, 5)
        self.page_num = 0
        self.p = mp.Pool(20)

    def __iter__(self):
        self.page_num = 0
        return self

    def __next__(self) -> ToriItemList:
        """
        Loops over classifieds pages on tori.fi for given topic
        """
        if self.page_num >= self.pages_max:
            raise StopIteration
        else:
            end_page = min(self.pages_max, self.page_num + self.pages_at_once)
            fetched = self.p.imap_unordered(self._fetch_page, range(self.page_num, end_page))
            self.page_num = end_page
            return functools.reduce(lambda x, y : x + y, fetched, self.parser.list_factory('fetch'))

    def _add_details(self, item: ToriItem) -> ToriItem:
        try:
            return self.parser.enrich(self._url_getter, item)
        except:
            self.logger.error('failed to fetch details: {}'.format(item))
            self.logger.error('Exception:\n{}'.format(traceback.format_exc()))

    def enrich(self, items: ToriItemList):
        try:
            enriched = self.p.imap_unordered(self._add_details, items)
            items.replace_items(list(enriched))
        except KeyboardInterrupt as e:
            raise e

    def _url_getter(self, url, user_msg=None):
        start = datetime.datetime.now()
        quoted = urllib.parse.quote(url, safe=':/&=?')
        try:
            with urllib.request.urlopen(quoted) as response:
                page_data = response.read()
                duration = (datetime.datetime.now() - start).total_seconds()
                user_msg = user_msg + ' -- ' if user_msg else ''
                self.logger.debug(f'{user_msg}{len(page_data) / 1000:.1f} KB, took {duration:.2f} s -- {quoted}')
                return page_data
        except KeyboardInterrupt as e:
            raise e
        except:
            self.logger.error('failed to fetch: {}'.format(quoted))
            self.logger.error('Exception:\n{}'.format(traceback.format_exc()))

    def _page_reader(self, page_num):
        url_base = 'https://www.tori.fi/'
        url_search_all = 'koko_suomi' + self.parser.topic
        url_search_string = ''
        page_pos = 'o=' + str(page_num)
        url_to_search = url_base + url_search_all + '?' + url_search_string + '&' + page_pos
        return self._url_getter(url_to_search)

    def _fetch_page(self, page_num) -> ToriItemList:
        html = self._page_reader(page_num)
        items = self.parser.parse(html)
        items.remove_buys()
        return items
