# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 22:11:17 2022

@author: mrgna
"""

import numpy as np
import matplotlib.pyplot as plt

import LinearRateModel
import TradePayments

if __name__ == '__main__':
    model = LinearRateModel.LinearRateModel()
    
    #Set calibration instruments
    calib_instruments = ['FRA 1M','FRA 3M','FRA 6M','FRA 1Y',
                         'swap 0B 2y','swap 0B 3y','swap 0B 4y','swap 0B 5y',
                         'swap 0b 7y','swap 0B 10y','swap 0b 15y','swap 0b 20y',
                         'swap 0b 30y',]
    calib_instruments_rates = [0.0098,0.0130,0.01399,0.01864,
                               0.01652,0.02019,0.02319,0.02577,
                               0.02995,0.03395,0.03753,0.03873,
                               0.03975,]
    model.model_data['CALIBINSTRUMENTS'] = (calib_instruments,calib_instruments_rates)
    
    #Calibrate
    print(model.calibrate())  
        
    #plot forward rates, zcb rates and zcb prices
    model.plot_model(0,30,'FORWARDRATES',200)
    model.plot_model(0,30,'ZCBRATES',200)
    model.plot_model(0,30,'ZCBPRICES',200)
    
    xs = np.linspace(0,30,200)
    ys = [model.get_forward_rate(x) for x in xs]
    plt.plot(xs,ys)
    plt.xlabel('Time')
    plt.title('Forward rates')
    plt.show()
    
    #plot zero rates
    xs = np.linspace(0,30,200)
    ys = [model.get_zcb_rate(x) for x in xs]
    plt.plot(xs,ys)
    plt.xlabel('Time')
    plt.title('ZCB Rates')
    plt.show()
    
    #plot zero prices
    xs = np.linspace(0,30,200)
    ys = [model.get_zcb_price(x) for x in xs]
    plt.plot(xs,ys)
    plt.xlabel('Time')
    plt.title('ZCB Curve')
    plt.show()
    
    #Price some trades in the model
    trades = [TradePayments.create_trade_from_string(s) for s in ["FRA 18M 0.02386",'SWAP 0B 3Y 0.02019']]
    for trade in trades:
        trade.print_trade()
    trades_pv = [LinearRateModel.get_trade_value(trade,model) for trade in trades]
    trades_rate = [LinearRateModel.get_trade_rate(trade,model) for trade in trades]