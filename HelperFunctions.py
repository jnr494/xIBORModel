# -*- coding: utf-8 -*-
"""
Created on Sun Jul 17 11:05:16 2022

@author: mrgna
"""

import numpy as np

#Tenor functions
def tenorstring_to_year(tenor):
    if isinstance(tenor,int) or isinstance(tenor,float):
        return float(tenor)
    
    tenor_base = tenor[-1]
    tenor_number = int(tenor[:-1])
    
    if tenor_base == 'Y':
        tenor_year = tenor_number
    elif tenor_base == 'M':
        tenor_year = tenor_number / 12
    elif tenor_base == 'B':
        tenor_year = tenor_number / 252
    else:
        print(tenor)
        tenor_year = 1/0
    
    return float(tenor_year)
    
#ZCB and forward rates   
def get_zcb_rate_from_zcb_price(zcb_price, tenor):
    tenor_year = tenorstring_to_year(tenor)
    zcb_rate = - np.log(zcb_price) / tenor_year
    return zcb_rate
    
def get_zcb_price_from_zcb_rate(zcb_rate, tenor):
    tenor_year = tenorstring_to_year(tenor)
    zcb_price = np.exp(-zcb_rate * tenor_year)
    return zcb_price
    
def get_forward_rate_from_zcb_rate(zcb_rate, forward_coverage, tenor):
    forward_coverage_year = tenorstring_to_year(forward_coverage)    
    zcb_price = get_zcb_price_from_zcb_rate(zcb_rate,tenor)    
    forward_rate = (1 / zcb_price - 1) / forward_coverage_year
    return forward_rate

def get_zcb_rate_from_forward_rate(forward_rate, forward_coverage, tenor):
    forward_coverage_year = tenorstring_to_year(forward_coverage)
    zcb_price = 1 / (1 + forward_coverage_year * forward_rate)
    zcb_rate = get_zcb_rate_from_zcb_price(zcb_price, tenor)
    return zcb_rate

