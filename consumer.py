from bs4 import BeautifulSoup
import urllib.request, urllib.error, urllib.parse
import re, traceback, logging, datetime

from items import ToriItemList, CarItemList, ToriItem


class ToriParser:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.details_supported = False
        self.topic = ''

    @staticmethod
    def _get_number(text):
        if not text:
            return None
        no_ws = ''.join(text.split())
        matches = re.findall(r'\d+', no_ws)
        return int(matches[0]) if matches else None

    def _category_parser(self, soup):
        return soup.find('a')['title'].split(':')[1].strip()

    def list_factory(self, *args, **kwargs):
        return ToriItemList(*args, **kwargs)

    def parse(self, html) -> ToriItemList:
        if not html:
            return ToriItemList('fail')
        soup = BeautifulSoup(html, 'html.parser')
        discarded = re.compile(r'(prisjakt|pp_item|listing_carousel)')
        accepted = re.compile(r'^item_\d+$')

        rows = soup.body.find_all('div', class_='item_row')
        items = ToriItemList('fetch')
        items_total = 0

        for row in rows:
            if not discarded.match(row.attrs['id']) and accepted.match(row.attrs['id']):
                items_total += 1
                try:
                    has_image = 'item_row_no_image' not in row.attrs['class']
                    item = {
                        'toriid': int(row['id'].split('_')[1]),
                        'description': row.find('div', class_='desc').a.text,
                        'price': row.find('p', class_='list_price').text,
                        'date': re.sub(r'[\n\t]', '', row.find('div', class_='date_image').text.strip()),
                        'imageurl': row.find('img', class_='item_image')['src'] if has_image else None,
                        'toriurl': row.find('div', class_='desc').a['href'].split('?')[0]
                    }

                    cat_geo = row.find('div', class_='cat_geo')
                    item['location'] = cat_geo.find_all('p')[0].text.strip()
                    item['buy_or_sell'] = cat_geo.find_all('p')[1].text.strip()
                    item['category'] = self._category_parser(cat_geo)

                    try:
                        item['price'] = ToriParser._get_number(item['price'])
                    except IndexError:
                        self.logger.debug('unknown price format: {0}'.format(item['price']))
                        item['price'] = None

                        self.logger.debug('parsed:\n{}\n{}\n\n'.format('-' * 70, row.prettify()))
                    items.add(ToriItem(**item))
                except (TypeError, AttributeError, ValueError, KeyError) as e:
                    self.logger.error('Unable to parse:\n{}\n{}\n\n'.format('-' * 70, row.prettify()))
                    self.logger.error('Exception:\n{}'.format(traceback.print_exc()))
        self.logger.debug('successfully parsed {0}/{1}'.format(len(items), items_total))
        return items

    def add_details(self, html, item: ToriItem):
        pass


class CarParser(ToriParser):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.details_supported = True
        self.topic = '/autot'

    def _category_parser(self, soup):
        return 'autot'

    def list_factory(self, *args, **kwargs):
        return CarItemList(*args, **kwargs)

    def parse(self, html) -> CarItemList:
        return CarItemList.create_from_another_list(super().parse(html))

    def add_details(self, html, item: ToriItem):
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
        sub_topic = soup('div', class_='sub_topic')[0]('div', class_='ad_param')
        det['car_description_extra'] = sub_topic[0].text if sub_topic else None
        det['car_info'] = soup('div', class_='body')[0].text.strip('\n').strip()
        det['car_info'] = ' '.join([line.strip() for line in det['car_info'].split('\n')])
        item.add(**det)


class ToriConsumer:

    def __init__(self, parser, max_pages):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parser = parser
        self.page_max = max_pages
        self.page_num = 0

    def __iter__(self):
        self.page_num = 0
        return self

    def __next__(self) -> ToriItemList:
        """
        Loops over classifieds pages on tori.fi for given topic
        """
        if self.page_num > self.page_max:
            raise StopIteration
        else:
            self.page_num += 1
            return self._fetch_page(self.page_num)

    def add_details(self, item: ToriItem):
        if self.parser.details_supported:
            html = self._url_getter(item.toriurl)
            self.parser.add_details(html, item)

    def _url_getter(self, url):
        start = datetime.datetime.now()
        quoted = urllib.parse.quote(url, safe=':/&=?')
        try:
            with urllib.request.urlopen(quoted) as response:
                page_data = response.read()
                end = datetime.datetime.now()
                duration_ms = (end - start).total_seconds()
                self.logger.info(
                    '{0} - {1:.1f} KB, took {2:.2g} s'.format(quoted, len(page_data) / 1000, duration_ms))
                return page_data
        except (urllib.error.URLError, UnicodeEncodeError) as e:
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
        items.sort_by_date()
        return items
