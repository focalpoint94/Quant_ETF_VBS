"""
VBS_BackTester_V4.py
Volatility Break-Through BackTest
<Functions>
0) 거래량 기준 ETF List 생성
1) 개별 종목의 yield 분포
2) 일평균 매수 종목 수 분포
3) 일 평균 전략 평균 수익률 분포
4) 누적 수익률
"""


from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import os
from pykrx import stock
from time import sleep
import json
import numpy as np
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta


"""
Functions
"""
def get_ETF_list(num_ETF=100):
    """
    :param num_ETF: 리스트 종목 수
    :return:
    연 평균 거래량 기준 상위 num_ETF개의 종목 리스트 저장 (ETFs.txt)
    """
    # web driver
    opt = webdriver.ChromeOptions()
    opt.add_argument('headless')
    drv = webdriver.Chrome('./chromedriver.exe', options=opt)
    drv.implicitly_wait(3)
    drv.get('https://finance.naver.com/sise/etf.nhn')
    bs = BeautifulSoup(drv.page_source, 'lxml')
    drv.quit()

    # df: 거래량 기준 모든 ETF
    table = bs.find_all('table', class_='type_1 type_etf')
    df = pd.read_html(str(table), header=0)[0]
    df = df.drop(columns=['Unnamed: 9'])
    df = df.dropna()
    df = df.sort_values(by='거래량', ascending=False)
    etf_td = bs.find_all('td', class_='ctg')
    etfs = {}
    for td in etf_td:
        s = str(td.a['href']).split('=')
        code = s[-1]
        etfs[td.a.text] = code
    company_names = []
    codes = []
    for i in range(len(df)):
        name = df.iloc[i]['종목명']
        company_names.append(name)
        codes.append(etfs[name])
    df.insert(1, 'code', codes)
    df_index = []
    for idx in range(len(df)):
        if "채" in df.iloc[idx]['종목명']:
            df_index.append(df.index[idx])
    df = df.drop(index=df_index, axis=0)
    code_list = list(df['code'])
    company_list = list(df['종목명'])

    # 연 평균 거래량 기준 상위 num_ETF개의 종목 리스트 저장 (ETFs.txt)
    tm_now = datetime.strftime(datetime.now().date(), "%Y%m%d")
    tm_past = datetime.strftime(datetime.now().date() - timedelta(days=360), "%Y%m%d")
    volume_list = []
    for code in code_list:
        try:
            sleep(1)
            temp = stock.get_etf_ohlcv_by_date(tm_past, tm_now, code, "m")
            volume_sum = 0
            for i in range(len(temp)):
                volume_sum += temp.iloc[i]['거래량']
            volume_list.append(volume_sum)
        except json.decoder.JSONDecodeError:
            pass
    for i in range(len(code_list)):
        code_list[i] = 'A' + code_list[i]
    data = {'codes': code_list, 'company': company_list, 'volumes': volume_list}
    df = pd.DataFrame(data=data)
    df = df.sort_values(by='volumes', ascending=False)
    df = df[:num_ETF]
    df.to_csv('ETFs.txt', index=False)

def calc_yield(**kwargs):
    """
    :param kwargs:
    code: 종목 코드
    fromDate: 시작일
    toDate: 종료일
    buy_start: '변동성돌파', '변동성돌파-전일상승', '변동성돌파-상승출발'
    K_val = 변동성 돌파 전략의 K 값
    sell_start: '당일종가', '익일시가'
    buy_spillage: 스필리지 (e.g. x: x호가 단위 만큼 매수 spillage 발생)
    sell_spillage: 스필리지 (e.g. x: x호가 단위 만큼 매도 spillage 발생)
    trading_fee: 거래 수수료 (e.g. 0.00015 (0.015%))
    :return:
    매수 리스트 [(df index, 매수가격), ...]
    매도 리스트 [(df index, 매도가격), ...]
    수익률 리스트 [(df index, 수익률), ...]
    코스피 수익률 리스트 [(df index, 코스피 수익률), ...]
    누적 수익률
    DataFrame
    """
    code = kwargs['code']
    fromDate = kwargs['fromDate']
    toDate = kwargs['toDate']
    buy_strat = kwargs['buy_strat']
    K_val = kwargs['K_val']
    sell_strat = kwargs['sell_strat']
    buy_spillage = kwargs['buy_spillage']
    sell_spillage = kwargs['sell_spillage']
    trading_fee = kwargs['trading_fee']

    """
    Load DataFrame (OHLCV)
    Get Unit-Bid-Price
    Load KOSPI DataFrame (OHLCV)
    """
    while True:
        try:
            sleep(1)
            df = stock.get_etf_ohlcv_by_date(fromDate, toDate, code)
            # unit_bid = get_unit_bid_price(code)
            unit_bid = 5
            # kospi_df = stock.get_index_ohlcv_by_date(fromDate, toDate, "1001")
            break
        except json.decoder.JSONDecodeError:
            pass

    """
    Returns
    buy_list: 매수 리스트
    [(i, 매수가1), ...]
    sell_list: 매도 리스트
    [(i, 매도가1), ...]
    yield_list: 수익률 리스트
    [(i, 수익률1), ...]
    kospi_yield_list: 코스피 수익률 리스트
    [(i, 코스피 수익률1), ...]
    culmulative_yield: 누적 수익률
    """
    buy_list = []
    sell_list = []
    yield_list = []
    kospi_yield_list = []
    culmulative_yield = 1

    """
    매수 전략
    """
    if buy_strat == '변동성돌파':
        for i in range(1, len(df) - 1):
            yesterday_high = df.iloc[i-1]['고가']
            yesterday_low = df.iloc[i-1]['저가']
            yesterday_sweep = yesterday_high - yesterday_low
            target_price = df.iloc[i]['시가'] + yesterday_sweep * K_val
            # 매수 가격 발생 여부 확인
            if df.iloc[i]['저가'] < target_price < df.iloc[i]['고가']:
                if target_price % unit_bid == 0:
                    buy_price = target_price + unit_bid * buy_spillage
                else:
                    buy_price = (target_price + unit_bid) // unit_bid * unit_bid + unit_bid * buy_spillage
                buy_list.append((i, buy_price))

    elif buy_strat == '변동성돌파-전일상승':
        for i in range(1, len(df) - 1):
            yesterday_high = df.iloc[i-1]['고가']
            yesterday_low = df.iloc[i-1]['저가']
            yesterday_sweep = yesterday_high - yesterday_low
            target_price = df.iloc[i]['시가'] + yesterday_sweep * K_val
            yesterday_open = df.iloc[i-1]['시가']
            yesterday_close = df.iloc[i-1]['종가']
            # 전일 상승 조건
            if yesterday_close > yesterday_open:
                # 매수 가격 발생 여부 확인
                if df.iloc[i]['저가'] < target_price < df.iloc[i]['고가']:
                    if target_price % unit_bid == 0:
                        buy_price = target_price + unit_bid * buy_spillage
                    else:
                        buy_price = (target_price + unit_bid) // unit_bid * unit_bid + unit_bid * buy_spillage
                    buy_list.append((i, buy_price))

    elif buy_strat == '변동성돌파-상승출발':
        for i in range(1, len(df) - 1):
            yesterday_high = df.iloc[i-1]['고가']
            yesterday_low = df.iloc[i-1]['저가']
            yesterday_sweep = yesterday_high - yesterday_low
            target_price = df.iloc[i]['시가'] + yesterday_sweep * K_val
            yesterday_close = df.iloc[i-1]['종가']
            # 상승 출발 조건
            if yesterday_close < df.iloc[i]['시가']:
                # 매수 가격 발생 여부 확인
                if df.iloc[i]['저가'] < target_price < df.iloc[i]['고가']:
                    if target_price % unit_bid == 0:
                        buy_price = target_price + unit_bid * buy_spillage
                    else:
                        buy_price = (target_price + unit_bid) // unit_bid * unit_bid + unit_bid * buy_spillage
                    buy_list.append((i, buy_price))

    """
    매도 전략
    """
    if sell_strat == '당일종가':
        for buy_pnt in buy_list:
            sell_list.append((buy_pnt[0], df.iloc[buy_pnt[0]]['종가']))
        # 수익률
        for i in range(len(buy_list)):
            sell_price = sell_list[i][1] - unit_bid * sell_spillage
            delta = ((1 - trading_fee) * sell_price - (1 + trading_fee) * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    elif sell_strat == '익일시가':
        for buy_pnt in buy_list:
            sell_list.append((buy_pnt[0] + 1, df.iloc[buy_pnt[0] + 1]['시가']))
        # 수익률
        for i in range(len(buy_list)):
            sell_price = sell_list[i][1] - unit_bid * sell_spillage
            delta = ((1 - trading_fee) * sell_price - (1 + trading_fee) * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    elif sell_strat == '당일손절+익일시가':
        for buy_pnt in buy_list:
            # 당일 손절
            if buy_pnt[1] > df.iloc[buy_pnt[0]]['종가']:
                sell_list.append((buy_pnt[0], df.iloc[buy_pnt[0]]['종가']))
            # 익일 시가
            else:
                sell_list.append((buy_pnt[0] + 1, df.iloc[buy_pnt[0] + 1]['시가']))
        # 수익률
        for i in range(len(buy_list)):
            sell_price = sell_list[i][1] - unit_bid * sell_spillage
            delta = ((1 - trading_fee) * sell_price - (1 + trading_fee) * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    """
    코스피 수익률
    """
    # for buy_pnt in buy_list:
    #     kospi_delta = (kospi_df.iloc[buy_pnt[0]]['종가'] - kospi_df.iloc[buy_pnt[0]]['시가']) / kospi_df.iloc[buy_pnt[0]]['시가']
    #     kospi_yield_list.append((buy_pnt[0], (1 + kospi_delta)))

    return buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df

def calc_yield_dist(**kwargs):
    """
    :param kwargs:
    code: 종목 코드
    fromDate: 시작일
    toDate: 종료일
    buy_start: '변동성돌파', '변동성돌파-전일상승', '변동성돌파-상승출발'
    K_val = 변동성 돌파 전략의 K 값
    sell_start: '당일종가', '익일시가'
    buy_spillage: 스필리지 (e.g. x: x호가 단위 만큼 매수 spillage 발생)
    sell_spillage: 스필리지 (e.g. x: x호가 단위 만큼 매도 spillage 발생)
    trading_fee: 거래 수수료 (e.g. 0.00015 (0.015%))
    :return:
    개별 종목 수익률의 기초 통계량 산출 및 Plot
    """
    buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df = calc_yield(**kwargs)
    _yield_list = []
    for i in range(len(yield_list)):
        _yield_list[i] = yield_list[i][1] * 100
    print('AVG: ', np.mean(_yield_list))
    print('STD: ', np.std(_yield_list))
    print('Max: ', np.max(_yield_list))
    print('Min: ', np.min(_yield_list))
    plt.hist(_yield_list, bins=100, range=(np.min(_yield_list), np.max(_yield_list)), color='r', edgecolor='black', linewidth=1.2)
    plt.xlabel('Yield')
    plt.xticks(np.arange(np.min(_yield_list), np.max(_yield_list), 0.5))
    plt.rc('axes', unicode_minus=False)
    plt.show()

def simulate_invest(**kwargs):
    """
    :param kwargs:
    code_list: 종목 코드 리스트
    fromDate: 시작일
    toDate: 종료일
    buy_start: '변동성돌파', '변동성돌파-전일상승', '변동성돌파-상승출발'
    K_val = 변동성 돌파 전략의 K 값
    sell_start: '당일종가', '익일시가'
    spillage: 스필리지 (e.g. x: x호가 단위 만큼 매수 spillage 발생)
    trading_fee: 거래 수수료 (e.g. 0.00015 (0.015%))
    max_stock_num: 일일 최대 보유 종목 수
    :return:
    - 일 평균 전략 수익률 분포 print
    - 일 평균 매수 횟수 분포 print
    - 예상 누적 수익률 return
    """
    all_yield_list = []
    code_list = kwargs['code_list']
    max_stock_num = kwargs['max_stock_num']

    for code in code_list:
        param_dict = kwargs
        param_dict['code'] = code
        _, _, yield_list, _, _, _ = calc_yield(**param_dict)
        all_yield_list.extend(yield_list)
    all_yield_list.sort(key=lambda x: x[0])
    max_idx = all_yield_list[-1][0]

    arr = []
    for i in range(max_idx+1):
        arr.append([])
    for yield_tuple in all_yield_list:
        arr[yield_tuple[0]].append(yield_tuple[1]*100)

    # 일일 최대 보유 종목 수 제약
    for i in range(1, max_idx):
        if len(arr[i]) > max_stock_num:
            random.shuffle(arr[i])
            arr[i] = arr[i][:max_stock_num]

    daily_count_list = []
    daily_yield_avg_list = []
    for i in range(1, max_idx):
        daily_count_list.append(len(arr[i]))
        if len(arr[i]) == 0:
            daily_yield_avg_list.append(0)
        else:
            daily_yield_avg_list.append(np.sum(arr[i])/max_stock_num)

    culmulative_yield = 1
    for i in range(1, max_idx):
        if len(arr[i]) != 0:
            culmulative_yield = culmulative_yield * (1 + (np.sum(arr[i])/max_stock_num)/100)

    print('* 일 평균 매수 종목 갯수 기초 통계랑 *')
    print('AVG: ', np.mean(daily_count_list))
    print('STD: ', np.std(daily_count_list))
    print('MAX: ', np.max(daily_count_list))
    print('MIN: ', np.min(daily_count_list))
    print('================================')
    print('* 일 평균 전략 수익률 기초 통계랑 *')
    print('AVG: ', np.mean(daily_yield_avg_list))
    print('STD: ', np.std(daily_yield_avg_list))
    print('MAX: ', np.max(daily_yield_avg_list))
    print('MIN: ', np.min(daily_yield_avg_list))
    print('================================')
    print('* 예상 누적 수익률: ', culmulative_yield)
    return culmulative_yield


"""
거래량 기준 상위 N 종목 리스트 생성
"""
# get_ETF_list(num_ETF=50)


"""
종목 리스트 내 개별 종목의 VBS 전략 수익률 산출
"""
df = pd.read_csv('ETFs.txt')
code_list = list(df['codes'])
company_list = list(df['company'])
strat_profit = []
for i in range(len(code_list)):
    code_list[i] = code_list[i][1:]
for code in code_list:
    param_dict = dict({
        'code': code,
        'fromDate': '20160701',
        'toDate': '20210630',
        'buy_strat': '변동성돌파',
        'K_val': 0.4,
        'sell_strat': '당일종가',
        # 'sell_strat': '익일시가',
        'buy_spillage': 0,
        'sell_spillage': 1,
        'trading_fee': 0.000088,
    })
    buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df = calc_yield(**param_dict)
    strat_profit.append(culmulative_yield)
data = {'종목코드': code_list, '종목명': company_list, '전략 수익률': strat_profit}
df = pd.DataFrame(data=data)
writer = pd.ExcelWriter('개별종목BackTesting.xlsx', engine='xlsxwriter')
df.to_excel(writer)
writer.close()


"""
Simulation
"""
# df = pd.read_csv('ETFs.txt')
# code_list = list(df['codes'])
# for i in range(len(code_list)):
#     code_list[i] = code_list[i][1:]
# print('*****************************')
# arr = []
# for i in range(5):
#     param_dict = dict({
#         'code_list': code_list,
#         'fromDate': '20160601',
#         'toDate': '20210530',
#         'buy_strat': '변동성돌파',
#         'K_val': 0.4,
#         'sell_strat': '당일종가',
#         # 'sell_strat': '당일종가',
#         # 'sell_strat': '익일시가',
#         'buy_spillage': 0,
#         'sell_spillage': 3,
#         'trading_fee': 0.000088,
#         'max_stock_num': 6,
#         })
#     cy = simulate_invest(**param_dict)
#     arr.append(cy)
# print(np.mean(arr))
