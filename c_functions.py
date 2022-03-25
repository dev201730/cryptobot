
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

# calculate_ema(df['Close'], 10) #to calculate EMA for every 10 values
# ema 50 is last 50 periods, ema 20 is last 20 periods
# NEED EMA 9, 14, 21, 55 ; 50, 200
# RETURNS an array
def i_ema(prices, days, smoothing=2):
    ema = [sum(prices[:days]) / days]
    for price in prices[days:]:
        ema.append( (price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))) )
    return ema

# FOR AVERAGE CANDLE PRICE IN THE SELECTED INTERVAL, CALCULATE MOVING AVG
def i_ma(values):
	basic_ma = float(sum(values)/len(values))
	return basic_ma

# AVERAGE DIFFERENCE IN PRICE BETWEEN CANDLES IN A SELECTED INTERVAL
# me sa levizin closes nga njera te tjetra
def i_ma_diff(values):
	differences_arr = np.diff(values)

	for i in range(len(differences_arr)):
		differences_arr[i] = abs(differences_arr[i])

	avg_diff = float(sum(differences_arr)/len(differences_arr))
	return avg_diff
	

'''
def calculate_macd():
	shortEMA - longEMA
	return

'''

'''

open_positions = {
                  0: { "in_position": False, "investment_in_usd": 200, "bought_quantity": 0, "bought_price": 0 },
                  1: { "in_position": False, "investment_in_usd": 100, "bought_quantity": 0, "bought_price": 0 },
                  2: { "in_position": False, "investment_in_usd": 200, "bought_quantity": 0, "bought_price": 0 } 
                 }
'''

def find_dict_inposition(the_dict , the_attr, the_attr_val):
	#output index of innerdict which satisfies condition
	output = None
	counter = 0
	for d in the_dict.values():
		if d[the_attr] == the_attr_val:
			output = counter
			break
		counter = counter + 1
	return output 


def find_dict_inposition_best_price(the_dict , the_attr, the_attr_val, price_attr, price_val):
	#output index of innerdict which satisfies condition
	output = None
	counter = 0
	for d in the_dict.values():
		if d[the_attr] == the_attr_val and d[price_attr] <= price_val:
			output = counter
			break
		counter = counter + 1
	return output 

def find_dict_inposition_stop_loss(the_dict , the_attr, the_attr_val, price_attr, price_val):
	#output index of innerdict which satisfies condition
	output = None
	counter = 0
	for d in the_dict.values():
		if d[the_attr] == the_attr_val and d[price_attr] > price_val:
			output = counter
			break
		counter = counter + 1
	return output 


# attributes: filename, symbol,  side, investment_in_usd,  bought_quantity,  bought_price, sell_price, profit
def keepRecordInFile(filename, symbol,  side, investment_in_usd,  bought_quantity,  bought_price, sell_price, profit):
    f = open(filename,"a")
    f.write("\n")

    today = dt.datetime.now()
    transaction_date = today.strftime("%m/%d/%Y %H:%M:%S")
    # symbol,  side, investment_in_usd,  bought_quantity,  bought_price, sell_price, profit
    myline = "symbol: "+symbol +", side: "+side+", in_USD: "+str(investment_in_usd)+", bought_quantity: "+str(bought_quantity)+", bought_price: "+str(bought_price)+", sell_price: "+str(sell_price)+", DT: "+transaction_date+", PROFIT: "+str(profit)
    f.write(myline)
    
    f.close()