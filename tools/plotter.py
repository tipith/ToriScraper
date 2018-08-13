import logging
from datetime import date, timedelta
import math

import pandas as pd
import matplotlib.pyplot as plt

import database


logger = logging.getLogger('plotter')


def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta


def plot_generic(datelist):
    dfs = {}
    for d in datelist:
        items = database.get_items(d)
        dfs[d] = pd.DataFrame.from_records(items, index='Date', columns=['Description', 'Date', 'Category', 'Price'])

    df = pd.DataFrame.from_records(items, index='Date', columns=['Description', 'Date', 'Category', 'Price'])

    fig, axes = plt.subplots(nrows=2, ncols=1)
    df[df.Price < 500].hist(ax=axes[0], color='k', alpha=0.5, bins=100)
    axes[0].set_title('All prices')

    for d in datelist:
        if not dfs[d].empty:
            temp_ser = dfs[d].index.time
            print(temp_ser)
            pd.to_datetime(dfs[d].set_index(temp_ser, inplace=True))
            print(dfs[d])
            print(temp_ser)
            dfs[d].Description.resample('10T').count().plot.line(ax=axes[1], color='k', alpha=0.5)

    axes[1].set_title('Items / 10 min')


def plot_categories():
    items = database.get_items(date)
    df = pd.DataFrame.from_records(items, index='Date', columns=['Description', 'Date', 'Category', 'Price'])

    gb = df.groupby(['Category'])

    # for cat in df.Category.unique():
    # does the same thing: data[data.Category == cat]
    # print(gb.get_group(cat))

    print(gb.count())

    plot_price_hist = False
    plot_date_hist = False

    cats = df.Category.unique()[:8]
    cols = 4
    rows = math.ceil(len(cats) / cols)

    if plot_price_hist:
        fig, axes = plt.subplots(nrows=rows, ncols=cols)
        plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
        for ind, cat in enumerate(cats):
            ax = axes[ind // cols, ind % cols]
            cat_items = gb.get_group(cat)
            cat_items[cat_items.Price < 1000].hist(ax=ax, color='k', alpha=0.5, bins=100)
            ax.set_title(cat)
            ax.set_xlim(0, 1000)

    if plot_date_hist:
        fig, axes = plt.subplots(nrows=rows, ncols=cols)
        plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
        for ind, cat in enumerate(cats):
            ax = axes[ind // cols, ind % cols]
            cat_items = gb.get_group(cat)
            items = cat_items.Description.resample('10T').count()
            items.hist(ax=ax, color='k', alpha=0.5, bins=100)
            ax.set_title(cat)


dates = list(perdelta(date.today() - timedelta(days=7), date.today(), timedelta(days=1)))
print(list(dates))
plot_generic(dates)
plt.show()
