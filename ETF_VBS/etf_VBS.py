
"""
etf_VBS.py
Volatility Break-Through Strategy
종목: ETP
"""
import requests
import json
import sys, ctypes
import win32com.client
from datetime import datetime
import time
import pandas as pd

cpCodeMgr = win32com.client.Dispatch('CpUtil.CpStockCode')
cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
cpStock = win32com.client.Dispatch('DsCbo1.StockMst')
cpOhlc = win32com.client.Dispatch('CpSysDib.StockChart')
cpBalance = win32com.client.Dispatch('CpTrade.CpTd6033')
cpCash = win32com.client.Dispatch('CpTrade.CpTdNew5331A')
cpOrder = win32com.client.Dispatch('CpTrade.CpTd0311')

def check_creon_system():
    """
    Creon Systen Check
    """
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('check_creon_system() : admin user -> Failed')
        return False
    if (cpStatus.IsConnect == 0):
        print('check_creon_system() : connect to server -> Failed')
        return False
    if (cpTradeUtil.TradeInit(0) != 0):
        print('check_creon_system(): init trade -> Failed')
        return False
    return True

def post_message(slack_data):
    """
    :param slack_data
    :return:
    특정 채널에 slack message를 보냄
    * 채널은 webhook_url로 선택
    """
    webhook_url = "********************************"
    response = requests.post(webhook_url, data=json.dumps(slack_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text))

def dbgout(message):
    """
    :param message
    :return:
    message를 cmd 및 slack에 표시합니다.
    """
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S]') + message
    slack_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": strbuf,
                    "emoji": True
                }
            }
        ]
    }
    post_message(slack_data)

def printlog(message, *args):
    """
    :param message:
    :param args:
    :return:
    message 와 args를 cmd에 표시합니다
    """
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)

def get_current_price(code):
    """
    :param code: 종목 코드
    :return:
    현재가, 매도호가, 매수호가
    """
    cpStock.SetInputValue(0, code)
    cpStock.BlockRequest()
    item = {}
    item['cur_price'] = cpStock.GetHeaderValue(11)
    item['ask'] = cpStock.GetHeaderValue(16)
    item['bid'] = cpStock.GetHeaderValue(17)
    return item['cur_price'], item['ask'], item['bid']

def get_ohlc(code, qty):
    """
    :param code: 종목 코드
    :param qty: 요청 데이터 개수 (ohlcv 날짜의 개수)
    :return:
    dataframe

    <참고>
    https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=102&page=1&searchString=CpSysDib.StockChart&p=8841&v=8643&m=9505
    """
    cpOhlc.SetInputValue(0, code)
    cpOhlc.SetInputValue(1, ord('2'))
    cpOhlc.SetInputValue(4, qty)
    cpOhlc.SetInputValue(5, [0, 2, 3, 4, 5])
    cpOhlc.SetInputValue(6, ord('D'))
    cpOhlc.SetInputValue(9, ord('1'))
    cpOhlc.BlockRequest()
    count = cpOhlc.GetHeaderValue(3)
    columns = ['open', 'high', 'low', 'close']
    index = []
    rows = []
    for i in range(count):
        index.append(cpOhlc.GetDataValue(0, i))
        rows.append([cpOhlc.GetDataValue(1, i), cpOhlc.GetDataValue(2, i),
                     cpOhlc.GetDataValue(3, i), cpOhlc.GetDataValue(4, i)])
    df = pd.DataFrame(rows, columns=columns, index=index)
    return df

def get_stock_balance(code, verbose=True):
    """
    :param code: 종목 코드 혹은 'ALL'
    :param verbose: log 출력 여부
    :return:
    1) 단일 종목
    종목명과 보유 수량을 반환
    2) ALL
    코드, 종목명, 보유 수량을 담은 리스트를 반환
    [{'code': -, 'name': -, 'qty'}, ...]

    <참고>
    https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=176&page=1&searchString=CpTrade.CpTd6033&p=8841&v=8643&m=9505
    """
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)         # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
    cpBalance.BlockRequest()
    if code == 'ALL' and verbose:
        dbgout('계좌명: ' + str(cpBalance.GetHeaderValue(0)))
        dbgout('결제잔고수량 : ' + str(cpBalance.GetHeaderValue(1)))
        dbgout('평가금액: ' + str(cpBalance.GetHeaderValue(3)))
        dbgout('평가손익: ' + str(cpBalance.GetHeaderValue(4)))
        dbgout('종목수: ' + str(cpBalance.GetHeaderValue(7)))
    stocks = []
    for i in range(cpBalance.GetHeaderValue(7)):
        stock_code = cpBalance.GetDataValue(12, i)  # 종목코드
        stock_name = cpBalance.GetDataValue(0, i)   # 종목명
        stock_qty = cpBalance.GetDataValue(15, i)   # 수량
        if code == 'ALL':
            if verbose:
                dbgout(str( i +1) + ' ' + stock_code + '(' + stock_name + ')'
                       + ':' + str(stock_qty))
            stocks.append({'code': stock_code, 'name': stock_name,
                           'qty': stock_qty})
        if stock_code == code:
            return stock_name, stock_qty
    if code == 'ALL':
        return stocks
    else:
        stock_name = cpCodeMgr.CodeToName(code)
        return stock_name, 0

def get_num_stocks():
    """
    :return:
    보유 종목 수
    """
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)         # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
    cpBalance.BlockRequest()
    return cpBalance.GetHeaderValue(7)

def get_stock_status(code):
    """
    :param code: 종목 코드
    :return:
    종목명 (str), 보유 수량 (int), 수익률 (double)
    <참고>
    https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=176&page=1&searchString=CpTrade.CpTd6033&p=8841&v=8643&m=9505
    """
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)         # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
    cpBalance.BlockRequest()
    for i in range(cpBalance.GetHeaderValue(7)):
        stock_code = cpBalance.GetDataValue(12, i)      # 종목코드
        stock_name = cpBalance.GetDataValue(0, i)       # 종목명
        stock_qty = cpBalance.GetDataValue(15, i)       # 수량
        stock_yield = cpBalance.GetDataValue(11, i)     # 수익률
        if stock_code == code:
            return stock_name, stock_qty, stock_yield
    stock_name = cpCodeMgr.CodeToName(code)
    return stock_name, 0, 0.0

def get_current_cash():
    """
    :return: 주문 가능 금액 (증거금 100%)
    """
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]          # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1)     # -1:전체, 1:주식, 2:선물/옵션
    cpCash.SetInputValue(0, acc)                # 계좌번호
    cpCash.SetInputValue(1, accFlag[0])         # 상품구분 - 주식 상품 중 첫번째
    cpCash.BlockRequest()
    return cpCash.GetHeaderValue(9)             # 증거금 100% 주문 가능 금액

def get_ETF_list(num_ETF=15):
    df = pd.read_csv('ETFs.txt')
    code_list = list(df['codes'])
    if len(code_list) > num_ETF:
        code_list = code_list[:num_ETF]
    return code_list

def get_target_price(code):
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.4
        return target_price
    except Exception as ex:
        dbgout("'get_target_price() -> exception! " + str(ex) + "'")
        return None

def get_moving_average(code, window):
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout('get_moving_avg(' + str(window) + ') -> exception! ' + str(ex))
        return None

def buy_etf(code):
    try:
        global bought_list                                              # 함수 내에서 값 변경을 하기 위해 global로 지정
        if code in bought_list:                                         # 매수 완료 종목이면 더 이상 안 사도록 함수 종료
            return False
        current_price, ask_price, bid_price = get_current_price(code)
        target_price = get_target_price(code)                           # 매수 목표가
        buy_qty = 0                                                     # 매수할 수량 초기화
        if ask_price > 0:                                               # 매수호가가 존재하면
            buy_qty = buy_amount // ask_price
        stock_name, stock_qty = get_stock_balance(code, verbose=False)  # 종목명과 보유수량 조회
        if target_price % 5 == 0:
            buy_price_limit = int(target_price)
        else:
            buy_price_limit = int((target_price + 5) // 5 * 5)
        if ask_price >= target_price:
            printlog(stock_name + '(' + str(code) + ') ' + str(buy_qty) +
                     'EA : ' + str(ask_price) + '>=' + str(target_price) + 'meets the buy condition!`')
            if buy_price_limit >= int(ask_price):
                printlog(stock_name + '(' + str(code) + ') ' + str(buy_qty) +
                         'EA : ' + str(buy_price_limit) + '>=' + str(ask_price) + 'meets the order condition!`')
                cpTradeUtil.TradeInit()
                acc = cpTradeUtil.AccountNumber[0]          # 계좌번호
                accFlag = cpTradeUtil.GoodsList(acc, 1)     # -1:전체,1:주식,2:선물/옵션
                cpOrder.SetInputValue(0, "2")               # 2: 매수
                cpOrder.SetInputValue(1, acc)               # 계좌번호
                cpOrder.SetInputValue(2, accFlag[0])        # 상품구분 - 주식 상품 중 첫번째
                cpOrder.SetInputValue(3, code)              # 종목코드
                cpOrder.SetInputValue(4, buy_qty)           # 매수할 수량
                cpOrder.SetInputValue(5, ask_price)         # 매수 희망 가격
                cpOrder.SetInputValue(7, "2")               # 주문조건 0:기본, 1:IOC, 2:FOK
                cpOrder.SetInputValue(8, "01")              # 주문호가 01:보통, 03:시장가
                                                            # 05:조건부, 12:최유리, 13:최우선
                """매수 주문 요청"""
                ret = cpOrder.BlockRequest()
                printlog('FOK 매수 ->', stock_name, code, buy_qty, '->', ret)
                if ret != 0:
                    printlog('주문 오류.')
                    return False
                if ret == 4:
                    remain_time = cpStatus.LimitRequestRemainTime
                    printlog('주의: 연속 주문 제한에 걸림. 대기 시간:', remain_time/1000)
                    time.sleep(remain_time/1000)
                    return False
                rqStatus = cpOrder.GetDibStatus()
                errMsg = cpOrder.GetDibMsg1()
                if rqStatus != 0:
                    printlog("주문 실패: ", rqStatus, errMsg)
                time.sleep(2)
                printlog('현금주문 가능금액 :', buy_amount)
                stock_name, bought_qty = get_stock_balance(code)
                printlog('get_stock_balance :', stock_name, stock_qty)
                if bought_qty > 0:
                    bought_list.append(code)
                    dbgout(" "+ str(stock_name) + ' : ' + str(code) +
                        " -> " + str(bought_qty) + "EA bought!" + " " + "(Target Price: " + str(target_price) + ")")
    except Exception as ex:
        dbgout("buy_etf("+ str(code) + ") -> exception! " + str(ex))

def sell_stock(code):
    """
    :param code: 종목 코드
    :return:
    최유리 IOC로 전량 매도
    """
    try:
        time_now = datetime.now()
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]          # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)     # -1:전체,1:주식,2:선물/옵션
        while True:
            t_now = datetime.now()
            t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            if t_now > t_exit:
                return False
            stock_name, stock_qty = get_stock_balance(code=code, verbose=False)
            if stock_qty == 0:
                dbgout("<" + str(stock_name) + ' , ' + str(code) +
                       "> 매도 완료")
                return True
            current_price, ask_price, bid_price = get_current_price(code)
            cpOrder.SetInputValue(0, "1")               # 1:매도, 2:매수
            cpOrder.SetInputValue(1, acc)               # 계좌번호
            cpOrder.SetInputValue(2, accFlag[0])        # 상품구분 - 주식 상품 중 첫번째
            cpOrder.SetInputValue(3, code)              # 종목코드
            cpOrder.SetInputValue(4, stock_qty)         # 매도할 수량
            # cpOrder.SetInputValue(5, bid_price)         # 매도 희망 가격
            cpOrder.SetInputValue(7, "1")               # 주문조건 0:기본, 1:IOC, 2:FOK
            cpOrder.SetInputValue(8, "12")              # 주문호가 01:보통, 03:시장가
            # 05:조건부, 12:최유리, 13:최우선
            ret = cpOrder.BlockRequest()
            dbgout('* 최유리 IOC 매도: ' + str(stock_name) + ', ' + str(code) + ', ' +
                   str(stock_qty) + ' (주문 ret: ' + str(ret) + ')')
            if ret == 1 or ret == 2:
                dbgout('주문 오류.')
            if ret == 4:
                remain_time = cpStatus.LimitRequestRemainTime
                dbgout('주의: 연속 주문 제한에 걸림. 대기 시간:' + str(remain_time /1000))
                time.sleep(remain_time / 1000)
            rqStatus = cpOrder.GetDibStatus()
            errMsg = cpOrder.GetDibMsg1()
            if rqStatus != 0:
                printlog("주문 실패: ", rqStatus, errMsg)
            time.sleep(30)
    except Exception as ex:
        dbgout("매도 함수 에러 발생 " + "(에러 내용: " + str(ex) + ")")
        return False

def sell_stock_list(code_list):
    """
    :param code_list: 매도 종목 코드 리스트
    :return:
    code_list 포트폴리오 매도
    """
    if len(code_list) != 0:
        for code in code_list:
            sell_stock(code)
            time.sleep(3)

def sell_all():
    try:
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]       # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
        while True:
            t_now = datetime.now()
            t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            if t_now > t_exit:
                return False
            stocks = get_stock_balance('ALL', verbose=False)
            total_qty = 0
            for s in stocks:
                total_qty += s['qty']
            if total_qty == 0:
                return True
            for s in stocks:
                if s['qty'] != 0:
                    cpOrder.SetInputValue(0, "1")           # 1:매도, 2:매수
                    cpOrder.SetInputValue(1, acc)           # 계좌번호
                    cpOrder.SetInputValue(2, accFlag[0])    # 주식상품 중 첫번째
                    cpOrder.SetInputValue(3, s['code'])     # 종목코드
                    cpOrder.SetInputValue(4, s['qty'])      # 매도수량
                    cpOrder.SetInputValue(7, "1")           # 조건 0:기본, 1:IOC, 2:FOK
                    cpOrder.SetInputValue(8, "12")          # 호가 12:최유리, 13:최우선

                    ret = cpOrder.BlockRequest()
                    printlog('최유리 IOC 매도', s['code'], s['qty'],
                        '-> cpOrder.BlockRequest() -> returned', ret)
                    if ret == 4:
                        remain_time = cpStatus.LimitRequestRemainTime
                        printlog('주의: 연속 주문 제한, 대기시간:', remain_time/1000)
                    rqStatus = cpOrder.GetDibStatus()
                    errMsg = cpOrder.GetDibMsg1()
                    if rqStatus != 0:
                        printlog("주문 실패: ", rqStatus, errMsg)
                time.sleep(1)
            time.sleep(30)
    except Exception as ex:
        dbgout("sell_all() -> exception! " + str(ex))

def get_buy_amount(target_buy_count, rate=0.99, verbose=False):
    """
    :param target_buy_count: 매수할 종목 수
    :param rate: 가용률 (국내 주식형 ETF: 소득세 면제)
    :return:
    """
    num_stocks = get_num_stocks()
    if target_buy_count == num_stocks:
        return 0
    total_cash = int(get_current_cash())  # 100% 증거금 주문 가능 금액 조회
    buy_amount = total_cash / (target_buy_count - num_stocks) * rate
    if verbose:
        printlog('100% 증거금 주문 가능 금액 :', total_cash)
        printlog('종목별 주문 금액 :', buy_amount)
    return buy_amount

if __name__ == '__main__':
    try:
        symbol_list = get_ETF_list(num_ETF=10)
        bought_list = []                                            # 매수 완료된 종목 리스트
        target_buy_count = 6                                        # 매수할 종목 수
        printlog('check_creon_system() :', check_creon_system())    # 크레온 접속 점검
        printlog('시작 시간 :', datetime.now().strftime('%m/%d %H:%M:%S'))
        soldout = False
        report1_flag = False
        report2_flag = False
        while True:
            t_now = datetime.now()
            t_9 = t_now.replace(hour=9, minute=1, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=2, second=0, microsecond=0)
            t_end = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
            today = datetime.today().weekday()
            if today == 5 or today == 6:
                sys.exit(0)
            if t_9 < t_now < t_start and not soldout:
                sell_all()
                get_buy_amount(target_buy_count=target_buy_count, rate=0.99, verbose=True)
                soldout = True
            if t_start < t_now < t_end:
                buy_amount = get_buy_amount(target_buy_count=target_buy_count, rate=0.99, verbose=False)
                for sym in symbol_list:
                    if buy_amount != 0:
                        buy_etf(sym)
                        time.sleep(1)
                """
                2회 보고
                - 오전 11:00
                - 오후 13:00
                """
                if not report1_flag and t_now.hour == 11 and t_now.minute == 0:
                    get_stock_balance('ALL')
                    report1_flag = True
                    time.sleep(5)
                if not report2_flag and t_now.hour == 13 and t_now.minute == 0:
                    get_stock_balance('ALL')
                    report2_flag = True
                    time.sleep(5)
            if t_exit < t_now:
                get_stock_balance('ALL')
                dbgout('거래 종료!')
                sys.exit(0)
            time.sleep(3)
    except Exception as ex:
        dbgout('main -> exception! ' + str(ex))