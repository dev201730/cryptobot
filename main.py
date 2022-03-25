import websocket, json, pprint, talib
import numpy as np
from binance.client import Client
from binance.enums import *

import pandas as pd
import matplotlib.pyplot as plt
import pandas_datareader as web
import datetime as dt

from credentials import API_KEY, API_SECRET

from c_functions import i_ema, i_ma, i_ma_diff
from c_functions import keepRecordInFile
from c_functions import find_dict_inposition, find_dict_inposition_best_price, find_dict_inposition_stop_loss


_SOCKET = "wss://stream.binance.com:9443/ws/"
_SYMBOL = 'ethusdt'
_INTERVAL = '1m'

# "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
SOCKET = _SOCKET + _SYMBOL + "@kline_" + _INTERVAL

client = Client(API_KEY, API_SECRET, tld='us')
client.API_URL = 'https://api.binance.com/api'

TRADE_SYMBOL = _SYMBOL.upper()




RSI_PERIOD = 15
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 30

STOP_LOSS = 0.992 # 1% of investment

open_positions = {
                  0: { "in_position": False, "investment_in_usd": 200, "bought_quantity": 0, "bought_price": 0 },
                  1: { "in_position": False, "investment_in_usd": 200, "bought_quantity": 0, "bought_price": 0 },
                  2: { "in_position": False, "investment_in_usd": 200, "bought_quantity": 0, "bought_price": 0 } 
                 }
pos_el_index = 0

closes = []


# TO GET THE LAST CLOSES TO CALCULATE RSI
klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "1 hour ago UTC")
#print(f"klines: {klines}")
#the 4th element is the close klines[i][4]
start_i = len(klines)-RSI_PERIOD
for i in range(start_i, len(klines)):
    closes.append(float(klines[i][4]))

print(f"closes: {closes}")


#--------------------------------------MOVING AVERAGE
MOVING_AVGS = []  #moving average price
MOVING_DIFFS = [] #moving average price differences

#--------------------------------------FIBO VARIABLES

maximum_price = 0
minimum_price = 0
level_1_up = 0
level_2_up = 0
level_3_up = 0
level_4_up = 0
level_5_up = 0

# TO GET THE LAST CLOSES TO CALCULATE RSI
fibo_klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "1 hour ago UTC")
fibo_closes = []

#the 4th element is the close klines[i][4]
#start_i = len(fibo_klines)-RSI_PERIOD
start_i = 0
for i in range(start_i, len(fibo_klines)):
    the_close = float(fibo_klines[i][4])
    fibo_closes.append(the_close)

#----------------------------------------------------------------FIBO

def produceFIBO():
    global fibo_klines, fibo_closes, closes
    global maximum_price, minimum_price
    global level_1_up, level_2_up, level_3_up, level_4_up, level_5_up
    
    #REMOVE FIRST ELEMENT
    fibo_closes.pop(0)
    #append latest value
    fibo_closes.append(closes[-1])

    maximum_price = max(fibo_closes)
    minimum_price = min(fibo_closes)

    difference = maximum_price - minimum_price

    #FOR AN UPWARD TREND
    level_1_up = maximum_price - difference * 0.236  
    level_2_up = maximum_price - difference * 0.382
    level_3_up = maximum_price - difference * 0.5
    level_4_up = maximum_price - difference * 0.618
    level_5_up = maximum_price - difference * 0.786

    #FOR A DOWNWARD TREND
    level_1_down = minimum_price + difference * 0.236  # = level_5_up
    level_2_down = minimum_price + difference * 0.382  # = level_4_up
    level_3_down = minimum_price + difference * 0.5    # = level_3_up
    level_4_down = minimum_price + difference * 0.618  # = level_2_up
    level_5_down = minimum_price + difference * 0.786  # = level_1_up

    #print the price at each level
    print('Level Percentage     Price ($)')
    print('00.0%\t\t', maximum_price)
    print('L1: 23.6%\t\t', level_1_up)
    print('L2: 38.2%\t\t', level_2_up)
    print('L3: 50.0%\t\t', level_3_up)
    print('L4: 61.8%\t\t', level_4_up) # GOLDEN Ratio
    print('L5: 78.6%\t\t', level_5_up)
    print('100.0%\t\t', minimum_price)


    #UPDATE THE MOVING AVERAGE: MOVING_AVG
    MOVING_AVGS.append( i_ma(fibo_closes[len(fibo_closes)-RSI_PERIOD:]) )
    print(f"MOVING AVERAGE: {MOVING_AVGS[-1]}")

    # avg difference between prices
    MOVING_DIFFS.append( i_ma_diff( fibo_closes[len(fibo_closes)-RSI_PERIOD:]) )
    print(f"MOVING AVERAGE DIFFS: {MOVING_DIFFS[-1]}")

    


#----------------------------------------------------------------FIBO


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
	global closes, open_positions, pos_el_index
	try:
		print("sending order")
		#For testing: order = "yes"
        #the following row makes the order on binance
		order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
		print(order)
		# attributes: filename, symbol, side,  investment_in_usd,  bought_quantity,  bought_price, sell_price, profit
		profit = (quantity * ( closes[-1] - open_positions[pos_el_index]["bought_price"] ) ) - (float(open_positions[pos_el_index]["investment_in_usd"]) * 0.00075)
		keepRecordInFile("transactions.txt", symbol, side, open_positions[pos_el_index]["investment_in_usd"], open_positions[pos_el_index]["bought_quantity"], open_positions[pos_el_index]["bought_price"], closes[-1], profit)
	except Exception as e:
		print("an exception occurred - {}".format(e))
		return False
	return True


def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, fibo_closes
    global maximum_price, minimum_price, MOVING_DIFFS
    global level_1_up, level_2_up, level_3_up, level_4_up, level_5_up
    global open_positions, pos_el_index

    # print('received message')
    json_message = json.loads(message)
    # print.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("CANDLE closed at {}".format(close))
        closes.append(float(close))

        produceFIBO()
        #print("closes:")
        #print(closes)

        if len(closes) > RSI_PERIOD:
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            #print("all rsis calculated so far")
            #print(rsi)
            last_rsi = round(rsi[-1], 0)
            print("the current rsi is {}".format(last_rsi))

            MIN_MARGIN = (MOVING_DIFFS[-1] *5)

            print(f"OPEN POSITIONS: {open_positions}")

            #STOP LOSS :  IF current-price / buy-price <= STOP_LOSS
            pos_el_index = find_dict_inposition_stop_loss(open_positions, "in_position", True, "bought_price", float(close))
            if pos_el_index != None: 
            	current_ratio = round( float( float(close) / float(open_positions[pos_el_index]["bought_price"]) ) , 3)
            	print(f"current ratio: {current_ratio}")
            	if current_ratio <= STOP_LOSS:
            		print("STOP LOSS! Sell! Sell! Sell!")
            		_order = order(SIDE_SELL, open_positions[pos_el_index]["bought_quantity"], TRADE_SYMBOL)
            		if _order:
            			open_positions[pos_el_index]["in_position"] = False
            			open_positions[pos_el_index]["bought_quantity"] = 0
            			open_positions[pos_el_index]["bought_price"] = 0

            # SELL WITH PROFIT  : IF current-price satisfies Minimum Profit Margin
            pos_el_index = find_dict_inposition_best_price(open_positions, "in_position", True, "bought_price", float(close) - MIN_MARGIN)
            if pos_el_index != None: 
                if float(close) - MIN_MARGIN >= float(open_positions[pos_el_index]["bought_price"] ):
                    print("Overbought! Sell! Sell! Sell!")
                    _order = order(SIDE_SELL, open_positions[pos_el_index]["bought_quantity"], TRADE_SYMBOL)
                    if _order:
                        open_positions[pos_el_index]["in_position"] = False
                        open_positions[pos_el_index]["bought_quantity"] = 0
                        open_positions[pos_el_index]["bought_price"] = 0
            
            # BUY : IF current-price satisfies RSI_OVERSOLD AND current-price is greater than FIBONACCI lowest level
            if last_rsi < RSI_OVERSOLD and float(close) >= (level_5_up + MIN_MARGIN) :
                pos_el_index = find_dict_inposition(open_positions, "in_position", False)
                if pos_el_index != None:
                    print("Oversold! Buy! Buy! Buy!")
                    open_positions[pos_el_index]["bought_price"] = float(close)
                    open_positions[pos_el_index]["bought_quantity"] = round( open_positions[pos_el_index]["investment_in_usd"] / float(close) , 3)
                    _order = order(SIDE_BUY, open_positions[pos_el_index]["bought_quantity"], TRADE_SYMBOL)
                    if _order:
                        open_positions[pos_el_index]["in_position"] = True

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()

