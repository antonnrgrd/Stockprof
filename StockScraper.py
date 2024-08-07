import requests as r
import json
import os
import pandas as pd
import re
import numpy as np
import time
import datetime
import random
import math
from concurrent.futures import ThreadPoolExecutor
currency_regex = "(Currency\sin\s)([A-Za-z()\.\s0-9]+)(</span>)"
currency_subregex_first_case = "(Currency\sin\s)([A-Za-z]+)\s\([0-9,]+\.[0-9]+\s([A-Z]+)\)"
currency_subregex_second_case = "(Currency\sin\s)([A-Z]+)"
'''Regex for getting current price is suprisingly tricky to get correct. Lots of false positives, the commented-out ones
were old candidates, saved just in case'''
#present_price_regex = "(FIN_TICKER_PRICE&quot;:&quot;)([0-9\.,]+)(&quot;)" (class=\"price\ssvelte-15b2o7n\">)([0-9\.]+)(</span>)
present_price_regex = "(data-field=\"regularMarketPrice\")(.+)(data-value=\")([0-9\.]+)(\"+)"
'''Note: this is a raw string as there are a ton of special characters, string delimiter mixing, escaping etc. And having it be a raw
string was the only way to make python interpret it correctly '''
dividend_yield_regex = r"(dividendYield\\\":{\\\"raw\\\":)([0-9\.]+)(,)"
one_year_target_price_regex = r"(targetMeanPrice.+)(\\\"fmt\\\":\\\")([0-9\.]+)"
sector_regex = r"(sector\\\":\\\")([a-zA-Z&\s]+)"
industry_regex = r"(industry\\\":\\\")([a-zA-Z&\s]+)"
'''Behold, the ugliest regex known to man! the reason why this is so unsightly is that if we want to extract the location of the company
we in the html code need to look for the adress, ending with the country in question. But there are so many ways you can specify an adress, with umlaut,
hyphen, punction, whitespace etc. so you need to be super general with what you are looking for.'''
country_regex = r"(country\\\":\\\")([a-zA-Z&\s]+)"
ex_rate_regex = "(Converted\sto<\/label><div>)([0-9\.+]+)(<)"
analyst_rating_regex = "(analysis\sshows\sthe\s)([a-z|\s]+)(\stoday)"
pb_ratio_regex=r"(priceToBook.+)(\\\"fmt\\\":\\\")([0-9\.]+)"
pe_ratio_regex=r"(trailingPE.+)(\\\"fmt\\\":\\\")([0-9\.]+)"
peg_ratio_regex = "(PEG Ratio\s(\s5yr expected\s)\s\s</p>\s<p class=\"value svelte-1n4vnw8\">)"

#Yahoo finance seems to have upped their game a bit to circumvent webscraping, so the workaround is
#adding this head info, curtesy to tsadigov from stackoverflow and reddit, that came with the workaround
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
class StockScraper:
    def __init__(self):
        self.conversion_factors = {}
        self.reference_currency = None
        self.scraper_readin_config()
    def scraper_readin_config(self):
        userhome = os.path.expanduser('~')
        with open(f"{userhome}/stockscraper_config/config_info.json") as f:
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
        summary = r.get(f"https://finance.yahoo.com/quote/{ticker}",headers=headers)
        profile = r.get(f"https://finance.yahoo.com/quote/{ticker}/profile?p={ticker}",headers=headers)
        ''' To handle the special cases when a stock is listed in a subunit e.g cents, we have to look
        at the chart info because after the update, the only place where they actually list the currency, is in the chart section
        '''
        chart = r.get(f"https://finance.yahoo.com/quote/{ticker}/chart?nn=1",headers=headers)
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
        summary = summary.text
        profile = profile.text
        chart = chart.text
        '''Annoyingly, some currencies are listed in subunits e.g pennies and cents instead of pounds and dollars
        this regex counters this case'''
        if "(" in re.search(currency_regex, chart).group(2):
            extracted_currency = re.search(currency_subregex_first_case, re.search(currency_regex, chart).group(0)).group(3)
        else:        
            extracted_currency = re.search(currency_subregex_second_case, chart).group(2)
        extracted_price = re.search(present_price_regex, summary).group(4)
        if re.search(dividend_yield_regex, summary):
            extracted_dividend_yield = re.search(dividend_yield_regex, summary).group(2)
        else:
            extracted_dividend_yield = np.NaN
        exracted_target_price = re.search(one_year_target_price_regex, summary).group(3)
        
        extracted_sector = re.search(sector_regex, profile).group(2)
        extracted_industry = re.search(industry_regex, profile).group(2)
        
        #extracted_country = re.search(country_regex, profile).groups()

       # extracted_country = extracted_country[-2] if extracted_country[-2] != None else extracted_country[-5] 
        extracted_country = re.search(country_regex, profile).group(2)
        stock_info["country"] = extracted_country
        stock_info["sector"] = extracted_sector
        stock_info["industry"] = extracted_industry
        stock_info["currency"] = extracted_currency.upper()
        stock_info["current_price"] = float(extracted_price.replace(",", "")) if extracted_price != "N/A" else np.NaN
        stock_info["target_price"] = float(exracted_target_price.replace(",", "")) if exracted_target_price != "N/A" else np.NaN
        stock_info["dividend_yield"] = extracted_dividend_yield if extracted_dividend_yield != "N/A" else np.NaN
        stock_info["pb_ratio"] = re.search(pb_ratio_regex, summary).group(3)
        pe_ratio_search = re.search(pe_ratio_regex, summary)
        stock_info["pe_ratio"] = pe_ratio_search.group(3) if pe_ratio_search != None else np.NaN
        stock_info["analyst_rating"] = self.scraper_get_stock_rating(ticker)
        return stock_info
    
    '''Large values are represented in shorthand with B for billion and M for million.
    This converts them to the actual values'''
    def scraper_convert_to_shorthand_number_to_real_number(self,value):
        if "M" in value:
            return float(value.replace("M", "")) * 1000000
        elif "B" in value:
            return float(value.replace("B", "")) * 1000000000
        else:
            return float(value)
    def scraper_get_value_in_ref_currency(self,value,stock_info):
        return self.conversion_factors[stock_info["currency"]] * self.scraper_convert_to_shorthand_number_to_real_number(value)
    
    def scraper_update_ticker(self,df,updated_info,index): 
        df.at[index,'country']=updated_info["country"]
        df.at[index,'currency']=updated_info["currency"]
        df.at[index,'sector']=updated_info["sector"]
        df.at[index,'industry']=updated_info["industry"]
        df.at[index,'target_price']=updated_info["target_price"]
        df.at[index,'current_price']= updated_info["current_price"] if updated_info["current_price"] != "N/A" else np.NaN
        df.at[index,'target_price']= updated_info["target_price"]
        df.at[index,'pb_ratio']=updated_info["pb_ratio"]
        df.at[index,'pe_ratio']=updated_info["pe_ratio"]
        df.at[index,'analyst_rating']=updated_info["analyst_rating"]
    def scraper_update_ticker_info(self,path):
        tickers = pd.read_csv(path)
        
              
        for ticker_index in tickers.index:
            print(f"Scraping {tickers.at[ticker_index, 'ticker']}")
            ticker_info = self.scraper_all_item_info(tickers.at[ticker_index, "ticker"])
            self.scraper_update_ticker(tickers,ticker_info,ticker_index)
            '''This time, when updating the tickers, it is important to tell we do not want to save the indexes as a coluumn, because each how we read it it
            we would for each iteration append a coulumn to the df when writing it out'''
        tickers.to_csv(f"{os.path.expanduser('~')}/stockscraper_config/items.csv",index=False)
        print("Completed webscrape successfully")


    def scraper_get_stock_rating(self,ticker):
        ticker = ticker.split(".", 1)[0].replace("-", "_")
        ticker_info = r.get(f"https://www.tradingview.com/symbols/{ticker}/", headers=headers).text
        return re.search(analyst_rating_regex,ticker_info).group(2)
   
            
    
    def scraper_advanced_update_ticker_info(self, tickers_df,index,advanced_updated_info):
        tickers_df.at[index,'pb_ratio'] = advanced_updated_info['pb_ratio']
        tickers_df.at[index,'pe_ratio'] = advanced_updated_info['pe_ratio']
        tickers_df.at[index,'peg_ratio'] = advanced_updated_info['peg_ratio']  
        tickers_df.at[index,'analyst_rating'] = advanced_updated_info['analyst_rating']    
        
def main():
    scraper = StockScraper()
   # scraper.check_items_daily()
    
if __name__ == "__main__":
    main()
    