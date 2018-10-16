#!/usr/bin/python3
#  coding: utf-8

import time
import random
import logging

from consumer import ToriConsumer, CarParser, ToriParser
from database import DBFactory

NUM_PAGES_TO_SEARCH = 50
NUM_KEEP_ITEMS = 4000

def get_new_items(_c):
    new_items = _c['consumer'].parser.list_factory('new', db=DBFactory.create())
    for items in _c['consumer']:
        diff_items = _c['old'].diff_to(items)
        if len(diff_items) == 0:
            break
        print(diff_items)
        _c['old'] += diff_items
        new_items += diff_items
    _c['old'].truncate_oldest(NUM_KEEP_ITEMS)
    return new_items


def _list_to_daterangetext(l):
    if not l[0] or not l[-1]:
        return 'timerange n/a'
    return '{} - {}'.format(l[0].date, l[-1].date)


def run():
    logger = logging.getLogger('main')
    logger.info('start tori.fi monitoring')
    consumers = [
        {'consumer': ToriConsumer(CarParser(), NUM_PAGES_TO_SEARCH)},
        {'consumer': ToriConsumer(ToriParser(), NUM_PAGES_TO_SEARCH)}
    ]

    for c in consumers:
        c['old'] = c['consumer'].parser.list_factory('old', db=DBFactory.create(), populate=True)
        logger.info('startup topic={}, {}'.format(c['consumer'].parser.topic, _list_to_daterangetext(c['old'])))

    while True:
        for c in consumers:
            new_items = get_new_items(c)
            if len(new_items):
                new_items.sort_by_date()
                for item in new_items:
                    if item.price:
                        c['consumer'].add_details(item)
                print(new_items)
                new_items.check_for_alarms()
                new_items.persist()

            logger.info('topic={}, {}/{} items ({} added), {}'.format(
                c['consumer'].parser.topic, len(c['old']), NUM_KEEP_ITEMS, len(new_items),
                _list_to_daterangetext(c['old'])))

        wait_time = 60 + random.randint(1, 60)
        time.sleep(wait_time)


if __name__ == '__main__':
    run()
