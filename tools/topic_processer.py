from pathlib import Path
import random, re, collections
import unidecode

import database


def get_topics():
    return [t['Description'] for t in database.get_descriptions()]


def print_stats(topic_list):
    print('{} total topics'.format(len(topics)))
    cnt = collections.Counter()
    for topic in topic_list:
        for word in topic.split():
            word = re.sub(r'[\W\s]+', '', word.lower(), re.UNICODE)
            cnt[word] += 1
    for ind, (word, count) in enumerate(cnt.most_common(100)):
        print('{} {:<20s} {}'.format(ind, word, count))



def save_topics(topic_list, name):
    fname = Path('topics_small.' + name + '.txt')
    print('{} topics written into {}'.format(len(topic_list), fname))
    with open(fname, 'w', encoding='ascii') as f:
        for t in topic_list:
            p1 = unidecode.unidecode(t.lower())
            p2 = p1.replace(' ', '_')
            p3 = re.sub(r'[\W\s]+', '', p2, re.UNICODE)
            #print('{} -> {} -> {} -> {}'.format(t, p1, p2, p3))
            f.write(' '.join(p3) + ' _ ')
    with open(fname, 'r', encoding='ascii') as f:
        dataset = set(f.read())
        print(len(dataset), ''.join(sorted(dataset)))


if __name__ == '__main__':
    topics = get_topics()
    random.shuffle(topics)
    print_stats(topics)

    size_scaler = 0.1
    train_size = int(len(topics) * 0.8 * size_scaler)
    valid_size = test_size = int(len(topics) * 0.1 * size_scaler)

    save_topics(topics[:train_size], 'train')
    save_topics(topics[train_size:train_size+valid_size], 'valid')
    save_topics(topics[train_size+valid_size:train_size+valid_size+test_size], 'test')
