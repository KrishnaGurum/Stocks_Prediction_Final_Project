"""
This module contains the code for downloading stock data from the Google Finance hidden API.
"""
import pandas as pd
import urllib.request
import datetime as dt


def get_google_data_for_stock(symbol, exchange, interval_seconds=86400, period='1d'):
    """
    Downloads the stock data for the instrument denoted by (symbol, exchange)

    :param symbol: The Google Finance 'code' for the stock
    :param exchange: The Google Finance 'index' to which the stock belongs
    :param interval_seconds: The number of seconds in one candle/time interval
    :param period: The period of time for which we should have data.
    :return: A pandas DataFrame containing the stock data and with a DateTimeIndex
    """
    url_root = 'http://www.google.com/finance/getprices?'
    url_root += 'q=' + symbol
    url_root += '&x=' + exchange
    url_root += '&i=' + str(interval_seconds)
    url_root += '&p=' + period
    url_root += '&f=d,o,h,l,c,v'
    url_root += '&df=cpct'

    print(url_root)

    with urllib.request.urlopen(url_root) as response:
        data = response.read().decode('ascii')

    # print(data)
    data = data.split('\n')

    # actual data starts at index = 7
    # first line contains full timestamp,
    # every other line is offset of period from timestamp
    parsd_data = []
    anchor_stamp = ''
    end = len(data)
    for i in range(7, end):
        c_data = data[i].split(',')
        if 'a' in c_data[0]:
            # first one record anchor timestamp
            anchor_stamp = c_data[0].replace('a', '')
            c_ts = int(anchor_stamp)
        else:
            try:
                coffset = int(c_data[0])
                c_ts = int(anchor_stamp) + (coffset * interval_seconds)
                parsd_data.append((dt.datetime.fromtimestamp(float(c_ts)), float(c_data[1]), float(c_data[2]), float(c_data[3]), float(c_data[4]), float(c_data[5])))
            except:
                pass  # for time zone offsets thrown into data
    df = pd.DataFrame(parsd_data)
    df.columns = ['ts', 'Close', 'High', 'Low', 'Open', 'Volume']
    df.index = df.ts
    del df['ts']
    return df
