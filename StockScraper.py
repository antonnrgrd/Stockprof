import requests as r
import json
import os
import pandas as pd
import re
from StockStatus import *
import numpy as np
from StockMailer import StockMailer

''' 
BeautifulSoup does some of the heavy work for us but what we 
'''
currency_regex = "( Currency in )(([A-Z])+)"
present_price_regex = "(data-pricehint=\"2\" value=\")(([0-9]|\.)+)"
dividend_yield_regex = "(\"DIVIDEND_AND_YIELD-value\">)(.+) \(([0-9]+\.[0-9]+%|N\/A)"
one_year_target_price_regex = "(data-test=\"ONE_YEAR_TARGET_PRICE-value\">)([0-9,]+\.[0-9]+|N\/A)"
sector_regex = "(Sector\(s\)<\/span>:\s<span class=\"Fw\(600\)\">)(([a-zA-Z]|\s)+)(<\/span>)"
industry_regex = "(Industry<\/span>:\s<span\sclass=\"Fw\(600\)\">)([a-zA-Z\s—;&]+)(<\/span>)"
#country_regex = "(<\/h3><div\sclass=\"Mb\(25px\)\"><p\sclass=\"D\(ib\) W\(47\.727%\) Pend\(40px\)\">(<br\/>)(.+)<br\/>)([a-zA-Z]+)(<br\/>)"
'''Behold, the ugliest regex known to man! the reason why this is so unsightly is that if we want to extract the location of the company
we in the html code need to look for the adress, ending with the country in question. But there are so many ways you can specify an adress, with umlaut,
hyphen, punction, whitespace etc. so you need to be super general with what you are looking for.'''
country_regex = "(class=\"D\(ib\) W\(47\.727%\) Pend\(40px\)\">)([a-zA-Z0-9\sæåøüÿëïöä\-,\.]+)(<br\/>)([a-zA-Z0-9\sæåøüÿëïöä\-,\.]+)(<br\/>)([a-zA-Z-\.\s]+)"
class StockScraper:
    def __init__(self):
        self.status = StockStatus()
        self.mailer = StockMailer()
    ''' '''
    @classmethod
    def scraper_all_item_info(self,ticker):
        stock_info = {}
        summary = r.get(f"https://finance.yahoo.com/quote/{ticker}?p={ticker}",headers={'User-Agent': 'Custom'}).text
        profile = r.get(f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}",headers={'User-Agent': 'Custom'}).text
        extracted_currency = re.search(currency_regex, summary).group(2)
        extracted_price = re.search(present_price_regex, summary).group(2)
        extracted_dividend_yield = re.search(dividend_yield_regex, summary).group(3)
        target_price = re.search(one_year_target_price_regex, summary).group(2)
        
        extracted_sector = re.search(sector_regex, profile).group(2)
        extracted_industry = re.search(industry_regex, profile).group(2).replace("&amp;", "&")
        
        extracted_country = re.search(country_regex, profile).group(6)
        
        stock_info["country"] = extracted_country
        stock_info["sector"] = extracted_sector
        stock_info["industry"] = extracted_industry
        stock_info["currency"] = extracted_currency
        stock_info["current_price"] = float(extracted_price)
        stock_info["target_price"] = target_price
        stock_info["dividend_yield"] = extracted_dividend_yield
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
        df.at[row["Unnamed: 0"],'current_price']= updated_info["current_price"] if updated_info["current_price"] != "N/A" else np.NaN
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
    