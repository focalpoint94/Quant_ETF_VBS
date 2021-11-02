"""
VBS_BackTester_V5.py
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
def _load_minute_series(code, date):
    """
    :param code_list: 종목 코드
    :param date: 일자
    :return:
    timestamp
    minute_data
    [[가격, volume], [가격, volume], ..., ]
    """
    timestamp = ['0901', '0902', '0903', '0904', '0905', '0906', '0907', '0908', '0909', '0910', '0911', '0912', '0913', '0914', '0915', '0916', '0917', '0918', '0919', '0920', '0921', '0922', '0923', '0924', '0925', '0926', '0927', '0928', '0929', '0930', '0931', '0932', '0933', '0934', '0935', '0936', '0937', '0938', '0939', '0940', '0941', '0942', '0943', '0944', '0945', '0946', '0947', '0948', '0949', '0950', '0951', '0952', '0953', '0954', '0955', '0956', '0957', '0958', '0959', '1000', '1001', '1002', '1003', '1004', '1005', '1006', '1007', '1008', '1009', '1010', '1011', '1012', '1013', '1014', '1015', '1016', '1017', '1018', '1019', '1020', '1021', '1022', '1023', '1024', '1025', '1026', '1027', '1028', '1029', '1030', '1031', '1032', '1033', '1034', '1035', '1036', '1037', '1038', '1039', '1040', '1041', '1042', '1043', '1044', '1045', '1046', '1047', '1048', '1049', '1050', '1051', '1052', '1053', '1054', '1055', '1056', '1057', '1058', '1059', '1100', '1101', '1102', '1103', '1104', '1105', '1106', '1107', '1108', '1109', '1110', '1111', '1112', '1113', '1114', '1115', '1116', '1117', '1118', '1119', '1120', '1121', '1122', '1123', '1124', '1125', '1126', '1127', '1128', '1129', '1130', '1131', '1132', '1133', '1134', '1135', '1136', '1137', '1138', '1139', '1140', '1141', '1142', '1143', '1144', '1145', '1146', '1147', '1148', '1149', '1150', '1151', '1152', '1153', '1154', '1155', '1156', '1157', '1158', '1159', '1200', '1201', '1202', '1203', '1204', '1205', '1206', '1207', '1208', '1209', '1210', '1211', '1212', '1213', '1214', '1215', '1216', '1217', '1218', '1219', '1220', '1221', '1222', '1223', '1224', '1225', '1226', '1227', '1228', '1229', '1230', '1231', '1232', '1233', '1234', '1235', '1236', '1237', '1238', '1239', '1240', '1241', '1242', '1243', '1244', '1245', '1246', '1247', '1248', '1249', '1250', '1251', '1252', '1253', '1254', '1255', '1256', '1257', '1258', '1259', '1300', '1301', '1302', '1303', '1304', '1305', '1306', '1307', '1308', '1309', '1310', '1311', '1312', '1313', '1314', '1315', '1316', '1317', '1318', '1319', '1320', '1321', '1322', '1323', '1324', '1325', '1326', '1327', '1328', '1329', '1330', '1331', '1332', '1333', '1334', '1335', '1336', '1337', '1338', '1339', '1340', '1341', '1342', '1343', '1344', '1345', '1346', '1347', '1348', '1349', '1350', '1351', '1352', '1353', '1354', '1355', '1356', '1357', '1358', '1359', '1400', '1401', '1402', '1403', '1404', '1405', '1406', '1407', '1408', '1409', '1410', '1411', '1412', '1413', '1414', '1415', '1416', '1417', '1418', '1419', '1420', '1421', '1422', '1423', '1424', '1425', '1426', '1427', '1428', '1429', '1430', '1431', '1432', '1433', '1434', '1435', '1436', '1437', '1438', '1439', '1440', '1441', '1442', '1443', '1444', '1445', '1446', '1447', '1448', '1449', '1450', '1451', '1452', '1453', '1454', '1455', '1456', '1457', '1458', '1459', '1500', '1501', '1502', '1503', '1504', '1505', '1506', '1507', '1508', '1509', '1510', '1511', '1512', '1513', '1514', '1515', '1516', '1517', '1518', '1519', '1520', '1530']
    minute_data = [[0, 0]] * len(timestamp)

    base_dir = 'C:/Git/Data/무수정/ETF_minute_Data/'
    A_code = 'A' + code
    code_dir = base_dir + A_code + '/'
    file_list = os.listdir(code_dir)
    date_list = [date[:-5] for date in file_list]
    if date not in date_list:
        df = pd.DataFrame()
    else:
        file_name = code_dir + date + '.json'
        df = pd.read_json(file_name, orient='table')

    for i in range(len(df)):
        if df.iloc[i]['time'] not in timestamp:
            continue
        time_idx = timestamp.index(df.iloc[i]['time'])
        minute_data[time_idx] = [df.iloc[i]['price'], df.iloc[i]['volumes']]

    return timestamp, minute_data

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
    sell_start: '당일종가', '익일시가', '당일손절+익일시가'
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
            timestamp, minute_data = _load_minute_series(code, datetime.strftime(df.index[buy_pnt[0]], "%Y%m%d"))
            sold = False
            for time_idx in range(len(timestamp)-6, len(timestamp)-1):
                price, volumes = minute_data[time_idx]
                if price != 0 and volumes != 0:
                    sell_list.append((buy_pnt[0], price))
                    sold = True
                    break
            if not sold:
                sell_list.append((buy_pnt[0], df.iloc[buy_pnt[0]]['종가']))
        # 수익률
        for i in range(len(buy_list)):
            sell_price = sell_list[i][1] - unit_bid * sell_spillage
            delta = ((1 - trading_fee) * sell_price - (1 + trading_fee) * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    elif sell_strat == '익일시가':
        for buy_pnt in buy_list:
            timestamp, minute_data = _load_minute_series(code, datetime.strftime(df.index[buy_pnt[0]+1], "%Y%m%d"))
            sold = False
            for time_idx in range(10):
                price, volumes = minute_data[time_idx]
                if price != 0 and volumes != 0:
                    sell_list.append((buy_pnt[0] + 1, price))
                    sold = True
                    break
            if not sold:
                sell_list.append((buy_pnt[0] + 1, df.iloc[buy_pnt[0]+1]['시가']))
        # 수익률
        for i in range(len(buy_list)):
            sell_price = sell_list[i][1] - unit_bid * sell_spillage
            delta = ((1 - trading_fee) * sell_price - (1 + trading_fee) * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    elif sell_strat == '당일손절+익일시가':
        for buy_pnt in buy_list:
            timestamp, minute_data = _load_minute_series(code, datetime.strftime(df.index[buy_pnt[0]], "%Y%m%d"))
            sold = False
            for time_idx in range(len(timestamp)-6, len(timestamp)-1):
                price, volumes = minute_data[time_idx]
                if price != 0 and volumes != 0:
                    sold = True
                    break
            close_price = price if sold else df.iloc[buy_pnt[0]]['종가']
            # 당일 손절
            if buy_pnt[1] > close_price:
                sell_list.append((buy_pnt[0], close_price))
            # 익일 시가
            else:
                timestamp, minute_data = _load_minute_series(code, datetime.strftime(df.index[buy_pnt[0]+1], "%Y%m%d"))
                sold = False
                for time_idx in range(10):
                    price, volumes = minute_data[time_idx]
                    if price != 0 and volumes != 0:
                        sold = True
                        break
                open_price = price if sold else df.iloc[buy_pnt[0]+1]['시가']
                sell_list.append((buy_pnt[0] + 1, open_price))
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
# get_ETF_list(num_ETF=30)


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
        'fromDate': '20190801',
        'toDate': '20210731',
        'buy_strat': '변동성돌파',
        'K_val': 0.4,
        # 'sell_strat': '당일종가',
        # 'sell_strat': '익일시가',
        'sell_strat': '익일시가',
        'buy_spillage': 0,
        'sell_spillage': 0,
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
#         # 'fromDate': '20190715',
#         'fromDate': '20210501',
#         'toDate': '20210709',
#         'buy_strat': '변동성돌파',
#         'K_val': 0.4,
#         # 'sell_strat': '당일종가',
#         'sell_strat': '익일시가',
#         # 'sell_strat': '당일손절+익일시가',
#         'buy_spillage': 0,
#         'sell_spillage': 0,
#         'trading_fee': 0.000088,
#         'max_stock_num': 6,
#         })
#     cy = simulate_invest(**param_dict)
#     arr.append(cy)
# print(np.mean(arr))
