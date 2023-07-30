import requests as r
import json
import os
import pandas as pd
import re
from StockStatus import *
import numpy as np
from StockMailer import StockMailer
from bs4 import BeautifulSoup
''' 
BeautifulSoup does some of the heavy work for us but what we 
'''
currency_regex = "( Currency in )(([A-Z])+)"
present_price_regex = "(data-pricehint=\"2\" value=\")(([0-9]|\.)+)"
dividend_yield_regex = "(\"DIVIDEND_AND_YIELD-value\">)(.+) \(([0-9]+\.[0-9]+%)"
one_year_target_price_regex = "(data-test=\"ONE_YEAR_TARGET_PRICE-value\">)([0-9]+\.[0-9]+)"
class StockScraper:
    def __init__(self):
        self.status = StockStatus()
        self.mailer = StockMailer()
    ''' '''
    @classmethod
    def scraper_all_item_info(self,ticker):
        stock_info = {}
        summary = r.get(f"https://finance.yahoo.com/quote/{ticker}?p={ticker}",headers={'User-Agent': 'Custom'}).text
        extracted_currency = re.search(currency_regex, summary).group(2)
        extracted_price = re.search(present_price_regex, summary).group(2)
        print(extracted_price)
        extracted_dividend_yield = re.search(dividend_yield_regex, summary).group(3)
        print(extracted_dividend_yield)
        target_price = re.search(one_year_target_price_regex, summary).group(2)
        print(target_price)
        
        stock_info["currency"] = extracted_currency
        stock_info["current_price"] = extracted_price
        statistics = r.get(f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}",headers={'User-Agent': 'Custom'}).text
        financials = r.get(f"https://finance.yahoo.com/quote/{ticker}/financials?p={ticker}",headers={'User-Agent': 'Custom'}).text
    def scraper_convert_to_numerical(self,value):
        if "M" in value:
            return int(value) * 1000000
        elif "B" in value:
            return int(value) * 1000000000
        else:
            return int(value)

    def check_items(self):
        
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir("{home}/stockscraper_config".format(home=userhome))
        ge_items = None
    #    try:      
        

        print(os.listdir())
        ge_items = pd.read_csv("items.csv",index_col=0)
        #except:
        #      print('error')
       #       return  
        for item in ge_items.to_dict(orient="records"):
            print(item)
            ge_info = r.get(item["url"])
            if ge_info.ok:
                response_info = ge_info.text
                '''To my recollection, Jagex sadly does not provide an API to neatly extract the GE prices
                to we are forced to manually find the price in the response HTML. This is not the prettiest regex
                but hey, it works.'''
                current_price = re.search("(<h3>Current Guide Price <span title=')([0-9]+)", response_info).group(2)
                item_name = re.search("<h2>(.+)<\/h2>", response_info).group(1)
                new_price = self.scraper_convert_to_numerical(current_price)
                price_change = None
                returns = None
                if item["current_price"] != np.Nan:
                    price_change = item["current_price"] /  new_price
                    if not np.isnan(item['current_holding']) and not np.isnan(item['initial_price']):
                        returns = (item['current_holding'] * item['initial_price']) / (item['current_holding'] * price_change)    
                if price_change and item["current_price"] and item['alert_threshold'] and price_change >= item['alert_threshold']:
                    self.status.add_formatted_alert(item["name"], item["current_price"], price_change. returns,item['current_holding'] )
                else:
                    self.status.add_formatted_info(item["name"], item["current_price"], price_change. returns,item['current_holding'] )
        self.mailer.ge_mailer_mail_update(self.status)
                        
                    
            
                
            
        
def main():
    scraper = StockScraper()
   # scraper.check_items_daily()
    
if __name__ == "__main__":
    main()
    