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
       # print(extracted_price)
        extracted_dividend_yield = re.search(dividend_yield_regex, summary).group(3)
        #print(extracted_dividend_yield)
        target_price = re.search(one_year_target_price_regex, summary).group(2)
        #print(target_price)
        
        stock_info["currency"] = extracted_currency
        stock_info["current_price"] = float(extracted_price)
        statistics = r.get(f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}",headers={'User-Agent': 'Custom'}).text
        financials = r.get(f"https://finance.yahoo.com/quote/{ticker}/financials?p={ticker}",headers={'User-Agent': 'Custom'}).text
        return stock_info
    def scraper_convert_to_numerical(self,value):
        if "M" in value:
            return int(value) * 1000000
        elif "B" in value:
            return int(value) * 1000000000
        else:
            return int(value)
    def scraper_update_ticker(self,row,df,updated_info): 
        df.at[row["Unnamed: 0"],'currency']=updated_info["currency"]
    def check_items(self):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir("{home}/stockscraper_config".format(home=userhome))
        tickers = pd.read_csv("items.csv")
        print(tickers)
        for item in tickers.to_dict(orient="records"):
            print(item)
            ticker_info = self.scraper_all_item_info(item["ticker"])
            price_change = None
            returns = None
            if item["current_price"] != np.NaN:
                price_change = item["current_price"] /  ticker_info["current_price"]
                if not np.isnan(item['holding']) and not np.isnan(item['initial_price']):
                    returns = (item['holding'] * item['initial_price']) / (item['current_holding'] * price_change)    
            if price_change and item["current_price"] and item['alert_threshold'] and price_change >= item['alert_threshold']:
                self.status.add_formatted_alert(item["ticker"], item["current_price"], price_change. returns,item['holding'] )
            else:
                self.status.add_formatted_info(item["ticker"], item["current_price"], price_change, returns,item['holding'] )
            self.scraper_update_ticker(item, tickers,ticker_info)
        #self.mailer.stock_mailer_mail_update(self.status)
        '''This time, when updating the tickers, it is important to tell we do not want to save the indexes as a coluumn, because each how we read it it
        we would for each iteration append a coulumn to the df when writing it out'''
        tickers.to_csv("items.csv",index=False)
                    
                    
            
                
            
        
def main():
    scraper = StockScraper()
   # scraper.check_items_daily()
    
if __name__ == "__main__":
    main()
    