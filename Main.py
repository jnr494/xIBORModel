# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 22:11:17 2022

@author: mrgna
"""

import LinearRateModel
import TradePayments

if __name__ == '__main__':
    model = LinearRateModel.LinearRateModel()
    
    #Set calibration instruments
    calib_instruments = ['FRA 1M','FRA 3M','FRA 6M','FRA 1Y',
                         'swap 0B 2y','swap 0B 3y','swap 0B 4y','swap 0B 5y',
                         'swap 0b 7y','swap 0B 10y','swap 0b 15y']
    calib_instruments_rates = [0.0098,0.0130,0.01399,0.01864,
                               0.01652,0.02019,0.02319,0.02577,
                               0.02995,0.03395,0.03753]
    model.model_data['CALIBINSTRUMENTS'] = (calib_instruments,calib_instruments_rates)
    
    #Calibrate
    print(model.calibrate(),'\n')  
        
    #plot forward rates, zcb rates and zcb prices
    model.plot_model(0,1,'FORWARDRATES',200)
    model.plot_model(0,1,'ZCBRATES',200)
    model.plot_model(0,1,'ZCBPRICES',200)
    
    #Price some trades in the model
    trade_strings = ["FRA 1M 0.02",'FRA 6M 0.02',"SWAP 0B 4Y 0.02",'SWAP 5Y 5Y 0.03']
    trades = [TradePayments.create_trade_from_string(s) for s in trade_strings]
    for trade in trades:
        trade.print_trade()
    #Trade PV
    trades_pv = [LinearRateModel.get_trade_value(trade,model) for trade in trades]
    #Corresponding swap rate or forward rate for trades
    trades_rate = [LinearRateModel.get_trade_rate(trade,model) for trade in trades]
    #deltavector of trade value based on model parameters in bp
    trade_value_dv01 = LinearRateModel.get_trade_deltavector(trades,model)*1e4
    #Impact to trade rate based in bump to model parameters in bp
    trade_rate_dv01 = LinearRateModel.get_trade_deltavector(trades,model,'RATE')*1e4
    
    #Get risks based in riskview 
    risk_view = calib_instruments
    risks =  LinearRateModel.get_trade_risk(trades,risk_view,model,return_pandas=True)*1e4
    print(risks)
    
    #Sanity check that dv01 and sum of risks are similar
    print(trade_value_dv01.sum(axis=0))
    print(risks.to_numpy().sum(axis=0))    
