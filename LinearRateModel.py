# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 23:20:03 2022

@author: mrgna
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import copy

from HelperFunctions import (tenorstring_to_year, get_zcb_rate_from_zcb_price)
import TradePayments


#Linear Rate Model Class
class LinearRateModel:
    
    def __init__(self):
        self.parameters = {'FORWARDRATES':np.array([[1,0.02]])}
        self.model_data = {'CALIBINSTRUMENTS':(['swap 0B 3y','swap 0B 4y','swap 0B 5y','swap 0B 10y'],
                                               [0.01652,0.02019,0.02319,0.02577,0.03395])}
        self.model_settings = {'FORWARDCOVERAGE':'6M'}

    def get_forward_rate(self, tenor): 
        tenor_year = tenorstring_to_year(tenor)
        spot_rate = np.interp(tenor_year, self.parameters['FORWARDRATES'][:,0], self.parameters['FORWARDRATES'][:,1])
        return spot_rate
    
    def get_zcb_rate(self, tenor):        
        zcb_price = self.get_zcb_price(tenor)
        zcb_rate = get_zcb_rate_from_zcb_price(zcb_price, tenor)
        return zcb_rate
        
    
    def get_zcb_price(self, tenor):
        forward_coverage_year = tenorstring_to_year(self.model_settings['FORWARDCOVERAGE'])
        
        #Get zcb price from time 0 to tenor % forward_coverage_year (stump)
        stump_coverage = tenor % forward_coverage_year
        zcb_price_stump = 1/(1+stump_coverage*self.get_forward_rate(0))
        
        #Get zcb prices for time tenor % forward_coverage_year to tenor
        forward_rate_points = np.arange(tenor-forward_coverage_year,-0.001,-forward_coverage_year)
        zcb_partial_prices = [1/(1+forward_coverage_year*self.get_forward_rate(time)) for time in forward_rate_points]
        #Calculate zcb price from 0 to tenor
        zcb_price = zcb_price_stump * np.product(zcb_partial_prices)
        
        return zcb_price
        
    
    def calibrate(self, optimizer_tol = 1e-11):
        #Get calib instrument from model_data
        calib_instruments_names = self.model_data['CALIBINSTRUMENTS'][0]
        calib_instruments_rates = np.array(self.model_data['CALIBINSTRUMENTS'][1])
        calib_instruments = []
        
        #Create trades from calib instruments
        for trades_string in calib_instruments_names:
            tmp_trade = TradePayments.create_trade_from_string(trades_string)
            tmp_trade.insert_variables()
            calib_instruments.append(tmp_trade)
            
        #Find model parameter dates and set initial paramter values
        model_parameter_dates = [instr.information['LASTFIXTIME'] for instr in calib_instruments]
        model_parameter_values = np.zeros(len(model_parameter_dates))
        self.parameters['FORWARDRATES'] = np.column_stack((model_parameter_dates,model_parameter_values))
        
        #define loss function and bounds
        def loss_function(parameter_values):
            self.parameters['FORWARDRATES'] = np.column_stack((model_parameter_dates,parameter_values))
            model_rates = np.array([get_trade_rate(instr, self) for instr in calib_instruments])
            loss = np.mean(np.square(model_rates - calib_instruments_rates))
            return loss
        
        bounds = [(-0.1,0.2) for _ in model_parameter_dates]
        
        #optimize
        result = minimize(loss_function, model_parameter_values ,bounds=bounds, tol=optimizer_tol)
        
        return result

    def plot_model(self, start_time, end_time, rate_type = 'FORWARDRATES', points = 100):
        #plot forward rates
        time_points = np.linspace(start_time, end_time,points)
        
        if rate_type.upper() == 'FORWARDRATES':
            model_output = [self.get_forward_rate(x) for x in time_points]
            plot_title = 'Forward rates'
        elif rate_type.upper() == 'ZCBRATES':
            model_output = [self.get_zcb_rate(x) for x in time_points]
            plot_title = 'ZCB rates'
        elif rate_type.upper() == 'ZCBPRICES':
            model_output = [self.get_zcb_price(x) for x in time_points]
            plot_title = 'ZCB prices'
        else:
            return 'ERROR UNKNOWN rate_type'
        
        plt.plot(time_points,model_output)
        plt.xlabel('Time')
        plt.title(plot_title)
        plt.show()


def get_trade_value(TradePayments, Model, leg = None):
    trade_pv = 0.0
    
    #loop over payments in trade
    for payment in TradePayments.payments:
        if leg is not None and payment.leg != leg:
            continue
         
        #Insert forward rate from model
        tmp_payment = payment.payment
        if payment.fixtime is not None:
            tmp_rate = Model.get_forward_rate(payment.fixtime)
            tmp_payment = tmp_payment.replace('XIBORRATE',str(tmp_rate))
        
        #Insert variables from trade (e.g. FIXEDRATE, STRIKE and/or SPREAD)
        for variable_name, variable_value in TradePayments.variables.items():
            tmp_payment = tmp_payment.replace(variable_name,str(variable_value))
        
        #Evaluat payment formula
        payment_value = eval(tmp_payment)
        
        #Discount and add to pv of payment to pv of trade
        tmp_discfactor = Model.get_zcb_price(payment.paytime)
        payment_pv = tmp_discfactor * payment_value
        trade_pv += payment_pv
        
    return trade_pv


def get_trade_rate(Trade, Model):
    tradetype = Trade.information['TRADETYPE']
    
    if tradetype == 'SWAP':
        pv_fixed_leg = get_trade_value(Trade,Model,0)
        pv_float_leg = get_trade_value(Trade,Model,1)
        trade_rate = - pv_float_leg / pv_fixed_leg * float(Trade.variables['FIXEDRATE'])
    elif tradetype == 'FRA':
        trade_rate = Model.get_forward_rate(Trade.payments[0].fixtime)
    else:
        trade_rate = 'ERROR'
        
    return trade_rate


def get_trade_deltavector(trades, Model, deriv_type = 'VALUE', leg = None, bump_size = 1e-4):
    if type(trades) is not list:
        trades = [trades]
    
    #set eval func for trade. Either rate or value
    deriv_type = deriv_type.upper()
    if deriv_type == 'VALUE':
        trade_eval = lambda trade, leg: get_trade_value(trade, Model, leg)
    elif deriv_type.upper() == 'RATE':
        trade_eval = lambda trade, leg: get_trade_rate(trade, Model)
    else:
        return "ERROR"
    
    #Get pv of trades
    trade_pv = np.array([trade_eval(trade, leg) for trade in trades])
    
    derivs = []
    original_parameters = copy.deepcopy(Model.parameters['FORWARDRATES'])
    
    for paramter_idx in range(len(Model.parameters['FORWARDRATES'])):
        Model.parameters['FORWARDRATES'][paramter_idx,1] += bump_size
        
        new_trade_pv = np.array([trade_eval(trade, leg) for trade in trades])
        tmp_deriv = (new_trade_pv - trade_pv)
        derivs.append(tmp_deriv)
        
        Model.parameters['FORWARDRATES'] = copy.deepcopy(original_parameters)
    
    derivs = np.stack(derivs,axis=0)
    
    return derivs
    
    
def get_trade_risk(trades, risk_instruments, Model, leg = None, bump_size=1e-4,return_pandas = False):
    if type(trades) is not list:
        trades = [trades]
    
    #Get parameter derivatives for TradePayments
    trade_derivs = get_trade_deltavector(trades, Model, 'VALUE', leg, bump_size) / bump_size

    #create trades for risk instruments:
    risk_trades = []
    for trades_string in risk_instruments:
        tmp_trade = TradePayments.create_trade_from_string(trades_string)
        tmp_trade.insert_variables()
        risk_trades.append(tmp_trade)        

    #Get parameter derivatives for risk_instruments
    risk_instruments_derivs = get_trade_deltavector(risk_trades, Model, 'RATE', None, bump_size) / bump_size
    
    #Calculate pseudo inverse of risk_instruments_derivs
    risk_derivs_inverse = np.linalg.pinv(risk_instruments_derivs)
    
    #Get risk
    trade_risk = (risk_derivs_inverse @ trade_derivs) * bump_size
    
    if return_pandas:
        return pd.DataFrame(np.round(trade_risk,8),index = [trade.information['TRADESTRING'] for trade in risk_trades], 
                            columns=[trade.information['TRADESTRING'] for trade in trades])
    else: #standard
        return trade_risk

if __name__ == '__main__':
    model = LinearRateModel()
    model.get_zcb_price(0.51)
    