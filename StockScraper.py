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
currency_regex_fallback = r"(currency\syf-15b2o7n\">)([A-Za-z]+)"
currency_regex = r"(currencyCode\\\":\\\")([A-Za-z]+)"
currency_subregex_first_case = "(Currency\sin\s)([A-Za-z]+)\s\([0-9,]+\.[0-9]+\s([A-Z]+)\)"
currency_subregex_second_case = "(Currency\sin\s)([A-Z]+)"
'''Regex for getting current price is suprisingly tricky to get correct. Lots of false positives, the commented-out ones
were old candidates, saved just in case'''
#present_price_regex = "(FIN_TICKER_PRICE&quot;:&quot;)([0-9\.,]+)(&quot;)" (class=\"price\ssvelte-15b2o7n\">)([0-9\.]+)(</span>)
present_price_regex = "(price\syf-15b2o7n\">)([0-9\.,]+)"
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
analyst_rating_regex =  r"technincal\sanalysis\sshows\sthe\s(strong\sbuy\srating|buy|neutral|sell|strong\ssell)"
pb_ratio_regex=r"(Price\/Book<\/td>\s<td\sclass=\"yf-kbx2lo\">)([0-9\.,]+)"
trailing_pe_ratio_regex=r"(Trailing P/E</td> <td class=\"yf-kbx2lo\">)([0-9\.,]+)"
five_year_expected_peg_ratio_regex = r"(PEG\sRatio\s\(5yr\sexpected\)</td>\s<td\sclass=\"yf-kbx2lo\">)([0-9\.,]+)"
profit_margin_regex = r"(profitMargins\\\":{\\\"raw\\\":)([0-9\.]+)"
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
                self.conversion_factors = self.scraper_get_currency_conv_factors(tickers, self.conversion_factors, config_info["ref_currency"])
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
    def scraper_get_currency_conv_factors(self,tickers:pd.DataFrame) -> dict:
        currencies = tickers.currency.unique()
        '''We cannot get the conversion factor for the reference currency, so we leave it out of the web scraping as getting
        the conversion factor for the currency itself leads to errors'''
        currencies = currencies[currencies != self.reference_currency]
        conversion_factors = dict()
        for currency in currencies:
            conversion_factor_text = r.get("https://wise.com/us/currency-converter/{currency}-to-{reference_currency}-rate?amount=1".format(currency=currency, reference_currency=self.reference_currency)).text
            factor = float(re.search(ex_rate_regex,conversion_factor_text).group(2).replace(",",""))
            conversion_factors[currency]=factor
        '''We include the conversion factor of the reference currency ( i.e 1), since it allow us to skimp on a lot of logic
        when converting the currencies to the reference currency'''
        conversion_factors[self.reference_currency] = 1
        return conversion_factors
    
    def scraper_get_web_page(self,url:str)  -> r.Response:  
        web_page_response = r.get(url, headers=headers)
        if not web_page_response.ok:
            num_attempts_to_get_page = 0
            while not web_page_response.ok and num_attempts_to_get_page < 10:
                web_page_response = r.get(url, headers=headers)
                num_attempts_to_get_page = num_attempts_to_get_page + 1 
                time.sleep(num_attempts_to_get_page)
            if not web_page_response.ok:
                raise Exception(f"Couldn\'t scrape {url}, got {web_page_response.status_code} ")
        return web_page_response
        
    def scraper_extract_web_info_to_dict(self, **web_pages):
        stock_info = {}
        '''Annoyingly, some currencies are listed in subunits e.g pennies and cents instead of pounds and dollars
        this regex counters this case'''

        extracted_currency = re.search(currency_regex, web_pages["stock_summary_as_text"])
        if extracted_currency == None:
            re.search(currency_regex_fallback, web_pages["stock_summary_as_text"]).group(2)
        else:
            extracted_currency = extracted_currency.group(2)

        extracted_price = re.search(present_price_regex, web_pages["stock_summary_as_text"]).group(2)
        if re.search(dividend_yield_regex, web_pages["stock_summary_as_text"]):
            extracted_dividend_yield = re.search(dividend_yield_regex, web_pages["stock_summary_as_text"]).group(2)
        else:
            extracted_dividend_yield = np.nan
            
        exracted_target_price_search = re.search(one_year_target_price_regex, web_pages["stock_summary_as_text"])
        
        extracted_sector_search = re.search(sector_regex, web_pages["stock_profile_as_text"])
        extracted_industry_search = re.search(industry_regex, web_pages["stock_profile_as_text"])
        
       
        extracted_country_search = re.search(country_regex, web_pages["stock_profile_as_text"])
        
        extracted_pb_ratio_search = re.search(pb_ratio_regex, web_pages["statistics_as_text"])
        
        extracted_profit_margin_search = re.search(profit_margin_regex, web_pages["statistics_as_text"])
        stock_info["country"] = extracted_country_search.group(2) if extracted_country_search != None else "undef"
        stock_info["sector"] = extracted_sector_search.group(2) if extracted_sector_search != None else "undef"
        stock_info["industry"] = extracted_industry_search.group(2) if extracted_industry_search != None else "undef"
        stock_info["currency"] = extracted_currency
        stock_info["current_price"] = float(extracted_price.replace(",", "")) if extracted_price != "N/A" else np.nan
        stock_info["target_price"] = float(exracted_target_price_search.group(3).replace(",", "")) if exracted_target_price_search != None else np.nan
        stock_info["dividend_yield"] = float(extracted_dividend_yield) if extracted_dividend_yield != "N/A" else np.nan
        stock_info["pb_ratio"] = float(extracted_pb_ratio_search.group(2)) if extracted_pb_ratio_search != None else np.nan
        trailing_pe_ratio_search = re.search(trailing_pe_ratio_regex, web_pages["statistics_as_text"])
        stock_info["trailing_pe_ratio"] = float(trailing_pe_ratio_search.group(2)) if trailing_pe_ratio_search != None else np.nan
        peg_ratio_growth_search = re.search(five_year_expected_peg_ratio_regex, web_pages["statistics_as_text"])
        stock_info["five_year_expected_peg_ratio"] = float(peg_ratio_growth_search.group(2)) if peg_ratio_growth_search  != None else np.nan
        stock_info["profit_margin"] = float(extracted_profit_margin_search.group(2)) if extracted_profit_margin_search  != None else np.nan
        return stock_info
    def scraper_update_ticker(self,ticker_index,tickers_dataframe):
        summary = self.scraper_get_web_page(f"https://finance.yahoo.com/quote/{tickers_dataframe.at[ticker_index, 'ticker']}").text
        profile = self.scraper_get_web_page(f"https://finance.yahoo.com/quote/{tickers_dataframe.at[ticker_index, 'ticker']}/profile?p={tickers_dataframe.at[ticker_index, 'ticker']}").text
        chart = self.scraper_get_web_page(f"https://finance.yahoo.com/quote/{tickers_dataframe.at[ticker_index, 'ticker']}/chart?nn=1").text
        statistics = self.scraper_get_web_page(f"https://finance.yahoo.com/quote/{tickers_dataframe.at[ticker_index, 'ticker']}/key-statistics/").text

        stock_info_as_dict = self.scraper_extract_web_info_to_dict(stock_chart_page_as_text=chart,stock_profile_as_text=profile,stock_summary_as_text=summary, statistics_as_text=statistics)
        stock_info_as_dict =  self.scraper_get_stock_rating(tickers_dataframe.at[ticker_index, 'ticker'],stock_info_as_dict)
        self.scraper_update_ticker_with_gathered_info(tickers_dataframe,stock_info_as_dict,ticker_index)
    def scraper_get_value_in_ref_currency(self,value,stock_info):
        return self.conversion_factors[stock_info["currency"]] * self.scraper_convert_to_shorthand_number_to_real_number(value)
    
    def scraper_update_ticker_with_gathered_info(self,tickers_dataframe,updated_ticker_info_dict,index):
        for ticker_info in updated_ticker_info_dict:
            tickers_dataframe.at[index,ticker_info] = updated_ticker_info_dict[ticker_info]

    def scraper_update_tickers(self,path):
        tickers = pd.read_csv(path)
        for ticker_index in tickers.index:
            print(f"Scraping {tickers.at[ticker_index, 'ticker']}")
            self.scraper_update_ticker(ticker_index,tickers)
            '''This time, when updating the tickers, it is important to tell we do not want to save the indexes as a coluumn, because each how we read it it
            we would for each iteration append a coulumn to the df when writing it out'''
        tickers.to_csv(f"{os.path.expanduser('~')}/stockscraper_config/items.csv",index=False)
        print("Completed webscrape successfully")


    def scraper_get_stock_rating(self,ticker,updated_ticker_info_dict):
        ticker = ticker.split(".", 1)[0].replace("-", "_")
        ticker_info = r.get(f"https://www.tradingview.com/symbols/{ticker}", headers=headers).text
        rating_search = re.findall(analyst_rating_regex, ticker_info)
        if rating_search:     
            updated_ticker_info_dict['analyst_rating'] = rating_search[0]
        else:
            updated_ticker_info_dict['analyst_rating'] = "unknown"
        return  updated_ticker_info_dict
   

    
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
    