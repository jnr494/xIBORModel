# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 19:38:11 2022

@author: mrgna
"""

from collections import namedtuple

from HelperFunctions import tenorstring_to_year

#trade cashflows functions and related
TradePayment = namedtuple('TradePayment', ['paytime','payment','fixtime','leg'])

class TradePayments():
    
    def __init__(self, tradetype,last_fixtime=None):
        self.payments = []
        self.variables = {}
        self.information = {'TRADETYPE':tradetype,'LASTFIXTIME':last_fixtime}
    
    def add_payment(self, paytime, payment, fixtime=None,indextenor='6M',leg=0):
        self.payments.append(TradePayment(paytime,payment,fixtime,leg))    
    
    def insert_variables(self):
        for idx, payment in enumerate(self.payments):
            for variable_name, variable_value in self.variables.items():
                self.payments[idx] = payment._replace(payment = payment.payment.replace(variable_name,str(variable_value)))
    
    def print_variables(self):
        print('Variables:')
        for variable_name, variable_value in self.variables.items():
            print(variable_name+'='+str(variable_value))
    
    def print_information(self):
        print('Information:')
        for info_name, info_value in self.information.items():
            print(info_name+'='+str(info_value))
        
    def print_payments(self):
        print('Payments:')
        for payment in self.payments:
            print('Paytime:',payment.paytime,'Fixtime:',payment.fixtime,'Payment:',payment.payment,'Leg:',payment.leg)
            
    def print_trade(self):
        self.print_information()
        self.print_variables()
        self.print_payments()
        print()

#FRA
def create_fra_payments(starttime, fixed_rate, indextenor='6M', notional=1):
    indextenor_year = tenorstring_to_year(indextenor)
    starttime_year = tenorstring_to_year(starttime)

    fra_payments = TradePayments("FRA",starttime_year)
    fra_payments.variables['FIXEDRATE'] = fixed_rate
    

    payment_string = str(notional) + '*' + str(indextenor_year) + '*(XIBORRATE-FIXEDRATE' + ')/(1+'+ str(indextenor_year) +'*XIBORRATE)'
    fra_payments.add_payment(starttime_year,payment_string,starttime_year,indextenor,0)
    return fra_payments

#Swap
def create_swap_payments(starttime, tenor, fixed_rate, indextenor='6M', notional = 1, leg = 'both'):
    tenor_year = tenorstring_to_year(tenor)
    indextenor_year = tenorstring_to_year(indextenor)
    starttime_year = tenorstring_to_year(starttime)
    endtime_year = starttime_year + tenor_year
    
    #Create trade and set FIXEDRATE
    last_fixtime = endtime_year - indextenor_year
    swap_payments = TradePayments("SWAP",last_fixtime)
    if abs(float(fixed_rate)) < 1e-9:
        fixed_rate = 1e-9
    swap_payments.variables['FIXEDRATE'] = str(fixed_rate)
    
    #Add fixed leg payments
    if leg in ['fixed','both']:
        numberof_fixed_legs = int(tenor_year / indextenor_year)
        tmp_payment_string = str(notional) + '*' + str(indextenor_year) + '*FIXEDRATE'
        for legidx in range(numberof_fixed_legs):
            tmp_paytime = endtime_year - legidx * indextenor_year
            swap_payments.add_payment(tmp_paytime,tmp_payment_string,None,indextenor,0)
    
    #Add floating leg payments
    if leg in ['floating','both']:
        numberof_floating_legs = int(tenor_year / indextenor_year)
        for legidx in range(numberof_floating_legs):
            tmp_paytime = endtime_year - legidx * indextenor_year
            tmp_fixtime = endtime_year - (legidx+1) * indextenor_year
            tmp_payment_string = '-' + str(notional) + '*' + str(indextenor_year) + '*XIBORRATE'
            swap_payments.add_payment(tmp_paytime,tmp_payment_string,tmp_fixtime,indextenor,1)
            
    return swap_payments
    
#Create Trade from string
def create_trade_from_string(trade_string):
    trade_string_split = trade_string.upper().split(' ')
    
    tradetype = trade_string_split[0]
    if tradetype == 'SWAP':
        starttime = trade_string_split[1]
        tenor = trade_string_split[2]
        if len(trade_string_split) == 4:
            fixed_rate = trade_string_split[3]
        else:
            fixed_rate = 1
        
        trade = create_swap_payments(starttime,tenor,fixed_rate)
            
    elif tradetype == 'FRA':
        starttime = trade_string_split[1]
        if len(trade_string_split) == 3:
            fixed_rate = trade_string_split[2]
        else:
            fixed_rate = 1
        
        trade = create_fra_payments(starttime,fixed_rate)
    else:
        trade = 'ERROR'
    
    return trade
    
if __name__ == '__main__':
    fra = create_fra_payments("1Y",0.02)
    swap = create_swap_payments("1Y","3Y","0.03")
    swap.print_payments()