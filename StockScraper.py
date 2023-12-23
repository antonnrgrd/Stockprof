import requests as r
import json
import os
import pandas as pd
import re
from StockStatus import *
import numpy as np
from StockMailer import StockMailer
import time
import datetime
import random
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
currency_regex = "(Currency\sin\s)([A-Za-z]+)\s\([0-9,]+\.[0-9]+\s[A-Z]+\)|(Currency\sin\s)([A-Z]+)"
currency_subregex_first_case = "(Currency\sin\s)([A-Za-z]+)\s\([0-9,]+\.[0-9]+\s([A-Z]+)\)"
currency_subregex_second_case = "(Currency\sin\s)([A-Z]+)"
'''Regex for getting current price is suprisingly tricky to get correct. Lots of false positives, the commented-out ones
were old candidates, saved just in case'''
present_price_regex = "(FIN_TICKER_PRICE&quot;:&quot;)([0-9\.,]+)(&quot;)"
dividend_yield_regex = "(\"DIVIDEND_AND_YIELD-value\">)(.+) \(([0-9]+\.[0-9]+%|N\/A)"
one_year_target_price_regex = "(data-test=\"ONE_YEAR_TARGET_PRICE-value\">)([0-9,]+\.[0-9]+|N\/A)"
sector_regex = "(Sector\(s\)<\/span>:\s<span class=\"Fw\(600\)\">)(([a-zA-Z]|\s)+)(<\/span>)"
industry_regex = "(Industry<\/span>:\s<span\sclass=\"Fw\(600\)\">)([a-zA-Z\s—;&,\-]+)"
'''Behold, the ugliest regex known to man! the reason why this is so unsightly is that if we want to extract the location of the company
we in the html code need to look for the adress, ending with the country in question. But there are so many ways you can specify an adress, with umlaut,
hyphen, punction, whitespace etc. so you need to be super general with what you are looking for.'''
country_regex = "(class=\"D\(ib\)\sW\(47\.727%\)\sPend\(40px\)\">)([^<>]+)(<br\/>)([^<>]+)((<br\/>)([^<>]+)(<br\/>)([^<>]+)(<br\/>)|(<br\/>)([^<>]+)(<br\/>))"

ex_rate_regex = "(Converted\sto<\/label><div>)([0-9\.+]+)(<)"

stock_rating_regex = "(<li\sclass=\"analyst__option\sactive\">)([a-zA-Z]+)(<\/li>)"
class StockScraper:
    def __init__(self,advanced_webscrape=False):
        self.conversion_factors = {}
        self.reference_currency = None
        self.scraper_readin_config()
        self.web_driver = None
        self.element_waiter = None
        '''Selenium adds a lot of "weight" to program. So we will only import it if we
        need to webscrape dynamic elements from Yahoo'''
        if advanced_webscrape:
            from selenium.webdriver.chrome.options import Options
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            '''Ensure chromer driver is in path '''
            chromedriver_autoinstaller.install()
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            self.web_driver = webdriver.Chrome(options=chrome_options)
            self.web_driver.maximize_window()
            self.element_waiter = WebDriverWait(self.web_driver , 10)
    def scraper_readin_config(self):
        userhome = os.path.expanduser('~')
        with open(f"{userhome}\\stockscraper_config\\config_info.json") as f:
            config_info = json.load(f)
            self.reference_currency = config_info["ref_currency"]
        
        
    def scraper_generate_dummy_returns(self):
        userhome = os.path.expanduser('~')
        returns = pd.read_csv(f"{userhome}/stockscraper_config/returns.csv")          
        base = datetime.datetime.today()
        date_list = date_list = [(base - datetime.timedelta(days=x)).strftime("%d-%m-%Y") for x in range(365 * 5)]
        return_values = [1000]
        for i in range((365 * 5) -1):
            return_values.append(return_values[-1] * random.uniform(1.01, 1.1))
       
        generated_holding_values = pd.DataFrame(return_values, index=date_list, columns=["holding_value"])

        returns = pd.concat([returns, generated_holding_values])
        '''This assumes that we generate values on an empty returns df. Pandas does not handle empty dataframes very well and among other
        things, setting the name of the index column seems to have no effect on empty dataframes, so we have to postpone it to here'''
        returns.index.name = "date"
        returns.to_csv(f"{userhome}/stockscraper_config/returns.csv")
    def scraper_get_daily_returns(self):
        '''Assumes value of holding is up to date'''
        present_date = datetime.datetime.now()
        present_date = present_date.strftime("%d-%m-%Y")
        userhome = os.path.expanduser('~')  
        os.chdir("{home}/stockscraper_config".format(home=userhome))
        tickers = pd.read_csv("items.csv")
        with open(f"{userhome}\\stockscraper_config\\config_info.json") as f:
                config_info = json.load(f)
                self.scraper_get_currency_conv_factors(tickers, self.conversion_factors, config_info["ref_currency"])
        '''Okay so this is a bit of a headache, we read in with index 0 as the first column is the date column, i,e our index
        but in the edge case we have no value, the result is an empty df so we need to re-create it.'''
        returns = pd.read_csv("returns.csv",index_col=0)
        #print(returns)
        if 'holding_value' not in returns.columns:
            returns = pd.DataFrame(columns = ['holding_value'])
        tickers["currency_amount"] = tickers["current_price"] * tickers["holding"]
        tickers["currency_amount"] = tickers["currency"].map(self.conversion_factors).mul(tickers["currency_amount"]) 
        holding_value_present = tickers.groupby(['ticker'])['currency_amount'].sum().sum()
        '''To save the date index, we use a hack where we first use the date as the index, then reset the index,
        making it a column so we can write it out without any issue to csv and then skip writing out the integer indexes'''
        returns.loc[present_date] = [holding_value_present]
        returns.index.name = "date"
        returns = returns.reset_index()
        returns.to_csv("returns.csv",index=False)
    def scraper_get_currency_conv_factors(self,tickers):
        currencies = tickers.currency.unique()
        '''We cannot get the conversion factor for the reference currency, so we leave it out of the web scraping as getting
        the conversion factor for the currency itself leads to errors'''
        currencies = currencies[currencies != self.reference_currency]
        for currency in currencies:
            conversion_factor_text = r.get("https://wise.com/us/currency-converter/{currency}-to-{reference_currency}-rate?amount=1".format(currency=currency, reference_currency=self.reference_currency)).text
            factor = float(re.search(ex_rate_regex,conversion_factor_text).group(2).replace(",",""))
            self.conversion_factors[currency]=factor
        '''We include the conversion factor of the reference currency ( i.e 1), since it allow us to skimp on a lot of logic
        when converting the currencies to the reference currency'''
        self.conversion_factors[self.reference_currency] = 1
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

        '''Assumes URL is formatted version of "Analysis" section to work '''
    def scraper_get_stock_rating(self,url):
        self.web_driver.get(url)
        '''Handle the cookie consent popup that appears.
        Find the button you want to click. This is done by finding an element with the name
        reject'''
        button = self.web_driver.find_element(By.NAME,'reject')
        '''Click the button - by first scrolling down and then clicking. Sidenote - the amount 
        required to scroll was a bit of a shot in the dark. This might not work for sufficiently
        big enough screens maybe?'''
        self.web_driver.execute_script("window.scrollTo(0, 200)")
        button.click()
        '''Wait until the dynamic elements have loaded. This sufficiently achieved
        by waiting for the recommended tickers to appear'''
        self.element_waiter.until(EC.presence_of_element_located((By.ID, "recommendations-by-symbol")))
        '''Quite annoyingly, the selenium webdriver is not competent to find web elements
        if the element in question is not physically visible on screen as seen from the view of an end user. So we scroll
        down to the end of the page to make it visible'''
        self.web_driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        anaylst_rating = self.web_driver.find_element(By.CSS_SELECTOR,"""[data-test="rec-rating-txt"]""")
        return float(anaylst_rating.get_attribute("innerHTML"))
                 
            
                
            
        
def main():
    scraper = StockScraper()
   # scraper.check_items_daily()
    
if __name__ == "__main__":
    main()
    