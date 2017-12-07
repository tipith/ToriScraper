#!/usr/bin/python3
#  coding: utf-8
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import re
import time
import datetime
import random
import logging

import gmail
import database

NUM_PAGES_TO_SEARCH = 25
NUM_KEEP_ITEMS = 4000

fetch_logger = logging.getLogger('fetch')
parse_logger = logging.getLogger('parse')
item_logger = logging.getLogger('item')
filter_logger = logging.getLogger('filter')
alarm_logger = logging.getLogger('alarm')


def fetch_tori_data(page):
    url_base = 'https://www.tori.fi/'
    url_search_all = 'koko_suomi'
    url_search_string = ''
    page_pos = 'o=' + str(page)
    url_to_search = url_base + url_search_all + '?' + url_search_string + '&' + page_pos
    start = datetime.datetime.now()
    try:
        with urllib.request.urlopen(url_to_search) as response:
            page_data = response.read()
            end = datetime.datetime.now()
            duration_ms = (end - start).total_seconds()
            fetch_logger.info('{0} - {1:.1f} KB, took {2:.2g} s'.format(url_to_search, len(page_data) / 1000, duration_ms))
            return page_data
    except urllib.error.UrlError:
        parse_logger.error('failed to fetch: {}'.format(page))
        return ''


def items_sort_by_date(items):
    return sorted(items, key=lambda k: k['date'])


def items_parse(html):

    soup = BeautifulSoup(html, 'html.pars    discarded = re.compile(r'(prisjakt|pp_item|listing_carousel)')
    accepted = re.compile(r'^item_\d+$')
er')
    rows = soup.body.find_all('div', class_='item_row')
    item_list = []
    items_parsed = 0
    items_total = 0

    for row in rows:
        if not discarded.match(row.attrs['id']) and accepted.match(row.attrs['id']):
            items_total += 1
            try:
                has_image = 'item_row_no_image' not in row.attrs['class']
                item = {
                    'id': int(row['id'].split('_')[1]),
                    'description': row.find('div', class_='desc').a.text,
                    'location': row.find('div', class_='cat_geo').find_all('p')[0].text.strip(),
                    'buy_or_sell': row.find('div', class_='cat_geo').find_all('p')[1].text.strip(),
                    'price': row.find('p', class_='list_price').text,
                    'date': re.sub(r'[\n\t]', '', row.find('div', class_='date_image').text.strip()),
                    'image_url': row.find('img', class_='item_image')['src'] if has_image else None,
                    'tori_url': row.find('div', class_='desc').a['href'].split('?')[0],
                    'category': row.find('div', class_='cat_geo').find('a')['title'].split(':')[1].strip()
                }

                try:
                    item['price'] = int(re.findall(r'\d+', ''.join(item['price'].split()))[0])
                except IndexError:
                    parse_logger.debug('unknown price format: {0}'.format(item['price']))
                    item['price'] = None

                parse_logger.debug('parsed:\n{}\n{}\n\n'.format('-'*70, row.prettify()))
                item_list.append(item)
                items_parsed += 1
            except (TypeError, AttributeError, ValueError) as e:
                parse_logger.error('Unable to parse:\n{}\n{}\n\n'.format('-'*70, row.prettify()))
                parse_logger.error('Exception:\n{}'.format(str(e)))

    # filter for selling items only
    item_list = list(filter(lambda item: item['buy_or_sell'] == 'Myydään', item_list))

    # modify strings representing dates to python datetimes
    months_fin = {1: 'tam', 2: 'hel', 3: 'maa', 4: 'huh', 5: 'tou', 6: 'kes',
                  7: 'hei', 8: 'elo', 9: 'syy', 10: 'lok', 11: 'mar', 12: 'jou'}
    months_fin2en = {'tam': 'Jan', 'hel': 'Feb', 'maa': 'Mar', 'huh': 'Apr', 'tou': 'May', 'kes': 'Jun',
                     'hei': 'Jul', 'elo': 'Aug', 'syy': 'Sep', 'lok': 'Oct', 'mar': 'Nov', 'jou': 'Dec'}
    today = datetime.date.today()
    yesterday = datetime.date.today() - datetime.timedelta(1)
    for item in item_list:
        if 'tänään' in item['date']:
            item['date'] = '{} {} {}'.format(today.day, months_fin[today.month], item['date'].split()[1])
        if 'eilen' in item['date']:
            item['date'] = '{} {} {}'.format(yesterday.day, months_fin[yesterday.month], item['date'].split()[1])
        # all dates are now in format 'DD Month HH:MM'
        date_split = item['date'].split()
        item['date'] = '{} {} {}'.format(date_split[0], months_fin2en[date_split[1]], date_split[2])
        item['date'] = datetime.datetime.strptime(item['date'], '%d %b %H:%M').replace(year=today.year)

    item_list = items_sort_by_date(item_list)
    parse_logger.debug('successfully parsed {0}/{1}'.format(items_parsed, items_total))
    return item_list


def item_to_str(item):
    return '{0} - {1} {2: >30} {3: >10} {4: <45} {5}'.format(
        item['id'], item['date'].strftime("%Y-%m-%d %H:%M"), item['location'], str(item['price']), item['description'], item['tori_url'])


def items_print(items):
    for item in items:
        item_logger.info(item_to_str(item))


# prequisite: 'items' needs to be sorted in chronological order
def items_keep_n_newest(items, n):
    if len(items) > n:
        filter_logger.info('removing {} oldest items'.format(len(items) - n))
        return items[-n:]
    return items


def items_check_for_alarm(items_to_check, alarms, testmode):
    alarms_sent = {}
    use_regex = True

    if use_regex:
        for alarm in alarms:
            if 'SearchPattern' in alarm and alarm['SearchPattern']:
                alarm['RegexSearchPattern'] = re.compile(alarm['SearchPattern'], re.IGNORECASE)
            if 'Location' in alarm and alarm['Location']:
                alarm['RegexLocation'] = re.compile(alarm['Location'], re.IGNORECASE)

    alarm_logger.debug('alarms: {}'.format(alarms))
    for item in items_to_check:
        for alarm in alarms:
            description_ok = False if 'SearchPattern' in alarm and alarm['SearchPattern'] else True
            location_ok = False if 'Location' in alarm and alarm['Location'] else True
            maxprice_ok = False if 'MaxPrice' in alarm and alarm['MaxPrice'] else True
            minprice_ok = False if 'MinPrice' in alarm and alarm['MinPrice'] else True

            if 'SearchPattern' in alarm and alarm['SearchPattern']:
                if use_regex:
                    if alarm['RegexSearchPattern'].match(item['description']):
                        description_ok = True
                elif alarm['SearchPattern'].lower() in item['description'].lower():
                    description_ok = True

            if description_ok and 'Location' in alarm and alarm['Location']:
                if use_regex:
                    if alarm['RegexLocation'].match(item['location']):
                        location_ok = True
                elif alarm['Location'].lower() in item['location'].lower():
                    location_ok = True

            if description_ok and location_ok and isinstance(item['price'], int):
                if 'MaxPrice' in alarm and alarm['MaxPrice'] and item['price'] < alarm['MaxPrice']:
                    maxprice_ok = True
                if 'MinPrice' in alarm and alarm['MinPrice'] and item['price'] > alarm['MinPrice']:
                    minprice_ok = True

            alarm_logger.debug('description {0: <20} {1: <20} item value {2: <20}'.format(
                alarm['SearchPattern'] if alarm['SearchPattern'] else 'None',
                'passed' if description_ok else 'failed',
                item['description']))
            alarm_logger.debug('location    {0: <20} {1: <20} item value {2: <20}'.format(
                alarm['Location'] if alarm['Location'] else 'None',
                'passed' if location_ok else 'failed',
                item['location']))
            alarm_logger.debug('maxprice    {0: <20} {1: <20} item value {2: <20}'.format(
                alarm['MaxPrice'] if alarm['MaxPrice'] else 'None',
                'passed' if maxprice_ok else 'failed',
                item['price'] if item['price'] else 'None'))
            alarm_logger.debug('minprice    {0: <20} {1: <20} item value {2: <20}'.format(
                alarm['MinPrice'] if alarm['MinPrice'] else 'None',
                'passed' if maxprice_ok else 'failed',
                item['price'] if item['price'] else 'None'))

            if all([description_ok, location_ok, maxprice_ok, minprice_ok]):
                if item['id'] not in alarms_sent or (item['id'] in alarms_sent and alarm['UserId'] not in alarms_sent[item['id']]):
                    if not testmode:
                        email = database.get_email(alarm['UserId'])
                        alarm_logger.info('alarm {} for "{}, {} eur"'.format(email, item['description'], item['price']))
                        gmail.send(email, 'Tori.fi: {}, {}'.format(item['description'], item['price']), item['tori_url'], None)
                        database.store_item_alarm(alarm['UserId'], item)
                    else:
                        alarm_logger.info('alarm found "{}, {} eur"'.format(item['description'], item['price']))
                    alarms_sent.setdefault(item['id'], []).append(alarm['UserId'])
                else:
                    alarm_logger.info('alarm already sent to UserId {} for "{}, {} eur"'.format(alarm['UserId'], item['description'], item['price']))

def run():
    filter_logger.info('start tori.fi monitoring')

    page_num = 1
    old_items = []
    new_items_all = []

    while True:
        items = items_parse(fetch_tori_data(page_num))

        old_item_ids = [item['id'] for item in old_items]
        new_items_query = [item for item in items if item['id'] not in old_item_ids]
        old_items += new_items_query
        new_items_all += new_items_query
        old_items = items_sort_by_date(old_items)

        filter_logger.debug('query new items {}/{}'.format(len(new_items_query), len(items)))

        if not len(new_items_query) or page_num > NUM_PAGES_TO_SEARCH:
            # process new items
            new_items_all = items_sort_by_date(new_items_all)
            items_print(new_items_all)
            items_check_for_alarm(new_items_all, database.get_alarms(), False)

            # truncate old items, and wait until next inspection round
            old_items = items_keep_n_newest(old_items, NUM_KEEP_ITEMS)
            wait_time = 60 + random.randint(1, 60)
            filter_logger.info('{} new items, total item count {}/{}, timerange {} - {}. now waiting for {} s'.format(
                len(new_items_all), len(old_items), NUM_KEEP_ITEMS, old_items[0]['date'], old_items[-1]['date'], wait_time))
            if len(new_items_query) and page_num > NUM_PAGES_TO_SEARCH:
                filter_logger.info('max page search count reached!')
            time.sleep(wait_time)
            page_num = 1
            new_items_all = []
        else:
            page_num += 1
            time.sleep(random.uniform(0.5, 1.0))

def test():
    filter_logger.info('start test mode')

    logging.getLogger().setLevel(logging.DEBUG)

    test_alarms = [{'AlarmId': 1,
                    'SearchPattern': 'sivuverho',
                    'MaxPrice': 500,
                    'MinPrice': None,
                    'UserId': 1,
                    'Location': 'Pohjois-savo'}]
    test_items = [{'id': 42464586,
                   'description': 'Sivuverhot',
                   'location': 'Pohjois-Savo',
                   'buy_or_sell': 'Myydään',
                   'price': 50,
                   'date': datetime.datetime(2017, 12, 2, 22, 46),
                   'image_url': 'https://d38a5rkle4vfil.cloudfront.net/image/lithumbs/02/0282065103.jpg',
                   'tori_url': 'https://www.tori.fi/pohjois-savo/Sivuverhot_42464586.htm',
                   'category': 'Sisustus ja huonekalut'}]

    items_check_for_alarm(test_items, test_alarms, True)


if __name__ == '__main__':
    run()
    #test()
