import requests as r
import json
import os
import pandas as pd
import re
from StockStatus import *
import numpy as np
from StockMailer import StockMailer
import time
#data-test="ASK-value">12,960.00 
#currency_regex = "( Currency in )(([A-Za-z])+)"
#(Currency in )([A-Za-z])+ \([0-9,]+\.[0-9]+ [A-Za-z]+\)
#currency_regex = "(Currency in )(([A-Za-z])+)"
#currency_regex = "( Currency in )(([A-Za-z])+)|(Currency in )([A-Za-z])+ \([0-9,]+\.[0-9]+ [A-Za-z]+\)"
currency_regex = "(Currency\sin\s)([A-Za-z]+)\s\([0-9,]+\.[0-9]+\s[A-Z]+\)|(Currency\sin\s)([A-Z]+)"
currency_subregex_first_case = "(Currency\sin\s)([A-Za-z]+)\s\([0-9,]+\.[0-9]+\s([A-Z]+)\)"
currency_subregex_second_case = "(Currency\sin\s)([A-Z]+)"
'''Regex for getting current price is suprisingly tricky to get correct. Lots of false positives, the commented-out ones
were old candidates, saved just in case'''
#present_price_regex = "(data-pricehint=\"2\" value=\")(([0-9]|\.)+)"
#present_price_regex = "(data-test=\"BID-value\">)([0-9\.,]+)"
present_price_regex = "(FIN_TICKER_PRICE&quot;:&quot;)([0-9\.,]+)(&quot;)"
dividend_yield_regex = "(\"DIVIDEND_AND_YIELD-value\">)(.+) \(([0-9]+\.[0-9]+%|N\/A)"
one_year_target_price_regex = "(data-test=\"ONE_YEAR_TARGET_PRICE-value\">)([0-9,]+\.[0-9]+|N\/A)"
sector_regex = "(Sector\(s\)<\/span>:\s<span class=\"Fw\(600\)\">)(([a-zA-Z]|\s)+)(<\/span>)"
industry_regex = "(Industry<\/span>:\s<span\sclass=\"Fw\(600\)\">)([a-zA-Z\s—;&,]+)(<\/span>)"
#country_regex = "(<\/h3><div\sclass=\"Mb\(25px\)\"><p\sclass=\"D\(ib\) W\(47\.727%\) Pend\(40px\)\">(<br\/>)(.+)<br\/>)([a-zA-Z]+)(<br\/>)"
'''Behold, the ugliest regex known to man! the reason why this is so unsightly is that if we want to extract the location of the company
we in the html code need to look for the adress, ending with the country in question. But there are so many ways you can specify an adress, with umlaut,
hyphen, punction, whitespace etc. so you need to be super general with what you are looking for.'''
country_regex = "(class=\"D\(ib\)\sW\(47\.727%\)\sPend\(40px\)\">)([^<>]+)(<br\/>)([^<>]+)((<br\/>)([^<>]+)(<br\/>)([^<>]+)(<br\/>)|(<br\/>)([^<>]+)(<br\/>))"

#"(class=\"D\(ib\)\sW\(47\.727%\)\sPend\(40px\)\">)([^<>]+)(<br\/>)([^<>]+)(<br\/>)([^<>]+)(<br\/>)([^<>]+)(<br\/>)"

#"(class=\"D\(ib\) W\(47\.727%\) Pend\(40px\)\">)([a-zA-Z0-9\sæåøüÿëïöä\-,\.]+)(<br\/>)([a-zA-Z0-9\sæåøüÿëïöä\-,\.]+)(<br\/>)([a-zA-Z-\.\s]+)"
class StockScraper:
    def __init__(self):
        self.status = StockStatus()
        self.mailer = StockMailer()
    ''' '''
    @classmethod
    def scraper_all_item_info(self,ticker):
        stock_info = {}
        summary = r.get(f"https://finance.yahoo.com/quote/{ticker}?p={ticker}",headers={'User-Agent': 'Custom'})
        profile = r.get(f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}",headers={'User-Agent': 'Custom'})
        if not summary.ok:
            failed_attempts = 0
            while not summary.ok and failed_attempts < 60:
                summary = r.get(f"https://finance.yahoo.com/quote/{ticker}?p={ticker}",headers={'User-Agent': 'Custom'})
                failed_attempts = failed_attempts + 1
                time.sleep(failed_attempts)
        if not profile.ok:
            failed_attempts = 0
            while not summary.ok and failed_attempts < 60:
                profile = r.get(f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}",headers={'User-Agent': 'Custom'})
                failed_attempts = failed_attempts + 1 
                time.sleep(failed_attempts)
        if not profile.ok or not summary.ok:
            print(profile.reason + str(profile.status_code))
            print(summary.reason + str(summary.status_code))
        summary = r.get(f"https://finance.yahoo.com/quote/{ticker}?p={ticker}",headers={'User-Agent': 'Custom'}).text
        profile = r.get(f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}",headers={'User-Agent': 'Custom'}).text
        '''Annoyingly, some currencies are listed in subunits e.g pennies and cents instead of pounds and dollars
        this regex counters this case'''
        if "(" in re.search(currency_regex, summary).group(0):
            extracted_currency = re.search(currency_subregex_first_case, re.search(currency_regex, summary).group(0)).group(3)
        else:        
            extracted_currency = re.search(currency_subregex_second_case, summary).group(2)
        extracted_price = re.search(present_price_regex, summary).group(2)
        extracted_dividend_yield = re.search(dividend_yield_regex, summary).group(3)
        exracted_target_price = re.search(one_year_target_price_regex, summary).group(2)
        
        extracted_sector = re.search(sector_regex, profile).group(2)
        extracted_industry = re.search(industry_regex, profile).group(2).replace("&amp;", "&")
        
        extracted_country = re.search(country_regex, profile).groups()

        extracted_country = extracted_country[-2] if extracted_country[-2] != None else extracted_country[-5] 
        
        stock_info["country"] = extracted_country
        stock_info["sector"] = extracted_sector
        stock_info["industry"] = extracted_industry
        stock_info["currency"] = extracted_currency.upper()
        stock_info["current_price"] = float(extracted_price.replace(",", "")) if extracted_price != "N/A" else np.NaN
        stock_info["target_price"] = float(exracted_target_price.replace(",", "")) if exracted_target_price != "N/A" else np.NaN
        stock_info["dividend_yield"] = extracted_dividend_yield if extracted_dividend_yield != "N/A" else np.NaN
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
        df.at[row["Unnamed: 0"],'country']=updated_info["country"]
        df.at[row["Unnamed: 0"],'currency']=updated_info["currency"]
        df.at[row["Unnamed: 0"],'sector']=updated_info["sector"]
        df.at[row["Unnamed: 0"],'industry']=updated_info["industry"]
        df.at[row["Unnamed: 0"],'target_price']=updated_info["target_price"]
        df.at[row["Unnamed: 0"],'current_price']= updated_info["current_price"] if updated_info["current_price"] != "N/A" else np.NaN
        df.at[row["Unnamed: 0"],'target_price']= updated_info["target_price"] 
    def check_items(self):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir("{home}/stockscraper_config".format(home=userhome))
        tickers = pd.read_csv("items.csv")
        for item in tickers.to_dict(orient="records"):
            print(item)
            ticker_info = self.scraper_all_item_info(item["ticker"])
            price_change = None
            returns = None
        #    if item["current_price"] != np.NaN:
         #       price_change = item["current_price"] /  ticker_info["current_price"]
         #       if not np.isnan(item['holding']) and not np.isnan(item['initial_price']):
         #           returns = (item['holding'] * item['initial_price']) / (item['holding'] * price_change)    
         #   if price_change and item["current_price"] and item['alert_threshold'] and price_change >= item['alert_threshold']:
         #       self.status.add_formatted_alert(item["ticker"], item["current_price"], price_change. returns,item['holding'] )
         #   else:
         #       self.status.add_formatted_info(item["ticker"], item["current_price"], price_change, returns,item['holding'] )
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
    