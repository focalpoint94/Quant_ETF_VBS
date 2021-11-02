# Quant_ETF_VBS
변동성 돌파 전략을 구현합니다. 단, ETF만 거래합니다.

ETF 거래용 Creon API 및 코드는 아래 도서 및 GITHUB를 참고하였습니다.

- 도서: http://www.yes24.com/Product/Goods/90578506?OzSrank=1

- GIT: https://github.com/INVESTAR/StockAnalysisInPython


# ETF_backtesting_V4
변동성 돌파 전략을 BackTest합니다.

## ETF.txt
백테스트할 ETF 코드 파일입니다. VBS_backtesting_V4.py에서 자동으로 생성합니다.
```
codes,company,volumes
A252670,KODEX 200선물인버스2X,60849618873.0
A114800,KODEX 인버스,11985725290.0
A122630,KODEX 레버리지,10510024930.0
A251340,KODEX 코스닥150선물인버스,10369868826.0
A233740,KODEX 코스닥150 레버리지,4841892805.0
A069500,KODEX 200,2054609655.0
A229200,KODEX 코스닥 150,1448268895.0
A252710,TIGER 200선물인버스2X,1156066679.0
```

## chromedriver.exe
현재 크롬 버젼에 맞는 크롬드라이버 설치가 필요합니다.

ETF.txt 파일을 생성함에 있어 웹 크롤링에 사용됩니다.


## 개별종목BackTesting.xlsx
결과 파일 예시입니다.
```
종목코드	종목명	전략 수익률
0	252670	KODEX 200선물인버스2X	0.790824343
1	114800	KODEX 인버스	0.477546108
2	122630	KODEX 레버리지	1.136677234
3	251340	KODEX 코스닥150선물인버스	0.647288605
4	233740	KODEX 코스닥150 레버리지	3.271532263
5	069500	KODEX 200	0.877931473
6	229200	KODEX 코스닥 150	1.160436325
7	252710	TIGER 200선물인버스2X	0.838926752
8	305720	KODEX 2차전지산업	2.006070634
9	102110	TIGER 200	0.912471778
```

## VBS_backTesting_V4.py
ETF Volatility Break-Through BackTest입니다.

총 4개의 기능이 구현되어 있습니다.
```
0) 거래량 기준 ETF List 생성
1) 개별 종목의 yield 분포
2) 일평균 매수 종목 수 분포
3) 일 평균 전략 평균 수익률 분포
4) 누적 수익률
```

- get_ETF_list(num_ETF=100)

거래량 기준 ETF List를 생성합니다.
```
param num_ETF: 리스트 종목 수
연 평균 거래량 기준 상위 num_ETF개의 종목 리스트 저장 (ETFs.txt)
```

- calc_yield(**kwargs):

개별 종목의 yield 분포를 산출합니다.
```
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
```

- calc_yield_dist(**kwargs):

개별 종목 수익률의 기초 통계량을 산출하고 Plot합니다.
```
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
```

- simulate_invest(**kwargs):

일 평균 전략 수익률 분포, 일 평균 매수 횟수 분포 및 예상 누적 수익률을 산출합니다.
```
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
```

# ETF_backtesting_V5
변동성 돌파 전략을 BackTest합니다.

V5는 V4와 기능상 동일합니다.

그러나 V5는 V4와 달리 분 단위 매매 시뮬레이션을 실행하며, 보다 정확한 백테스트 결과를 산출해냅니다.

(대신 백테스트 시간이 더 오래 소요됩니다.)

* ETF 분 단위 데이터가 필요합니다.

* 데이터를 다운받은 후, 코드에서 아래 경로를 수정하십시오.

** 경로: base_dir = 'C:/Git/Data/무수정/ETF_minute_Data/'

** 데이터 다운로드: https://github.com/focalpoint94/Quant_Price_Data_Crawling)

## 20190715~20210709_익일시가_6.txt
실행 로그 예시입니다.
```
*****************************
* 일 평균 매수 종목 갯수 기초 통계랑 *
AVG:  4.104081632653061
STD:  1.8885756628084662
MAX:  6
MIN:  0
================================
* 일 평균 전략 수익률 기초 통계랑 *
AVG:  0.3182327265434943
STD:  1.3917342703417503
MAX:  10.899361778080324
MIN:  -5.779333292988507
================================
* 예상 누적 수익률:  4.527922156270048
* 일 평균 매수 종목 갯수 기초 통계랑 *
AVG:  4.104081632653061
STD:  1.8885756628084662
MAX:  6
MIN:  0
================================
* 일 평균 전략 수익률 기초 통계랑 *
AVG:  0.323282139760651
STD:  1.3332645582708555
MAX:  10.653204171025761
MIN:  -5.779333292988507
================================
* 예상 누적 수익률:  4.658047140835219
* 일 평균 매수 종목 갯수 기초 통계랑 *
AVG:  4.104081632653061
STD:  1.8885756628084662
MAX:  6
MIN:  0
================================
* 예상 누적 수익률:  4.87712545481678
```

## AutoConnect.py
크레온에 자동 로그인합니다.

## etf_VBS.py
크레온을 통해 ETF 변동성 돌파 전략을 실행합니다.

32bit python 환경 세팅 및 slack 연동이 필요합니다.

자세한 내용은 위의 서적을 참고하기 바랍니다.

## etf_VBS_당일손절_익일시가매도.py
손절 및 익일 시가 매도를 적용한 version입니다.

## etf_VBS_당일종가.py
당일 종가 매도 version입니다.

## etf_VBS_익일시가.py
익일 시가 매도 version입니다.
