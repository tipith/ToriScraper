import datetime


def run():
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
