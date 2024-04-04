import argparse
from pathlib import Path
import os
import json
import platform
import pandas as pd
import numpy as np
from StockScraper import *
import sys
from StockProf import StockProfiler
attr_index_mapping = {'ticker':0,'currency':1, 'current_price':2, 'initial_price':3, 'holding':4,'alert_threshold':5}
class StockScrapeConfig:
    def setup_scraper_script(self):
        os = platform.system()
        if os.lower() == "windows":
            pass
        elif os.lower() == "linux":
            pass
    def config_setup(self,ref_currency):
        '''Makes some assumptions that aren't always true. There is no constraint that requires the username to appear in the homedir path on Linux. 
        It just happens to be the case most of the time, but a sysadmin can set a user's homedir to whatever they want '''
        userhome = os.path.expanduser('~')          
        os.chdir(userhome)
        if not os.path.exists("stockscraper_config"):
            os.makedirs("stockscraper_config")
        os.chdir("stockscraper_config")
        with open('config_info.json', 'w') as f:
            json.dump({"error_state": False, 'ref_currency':ref_currency.upper(), "row_id": None},f)
        tickers = pd.DataFrame(columns = ['ticker', 'currency', 'current_price', 'initial_price', 'holding', 'target_price','sector','industry', 'country','analyst_rating', 'pb_ratio','pe_ratio','peg_ratio','ev_ebitda_ratio','market_cap_in_ref_currency','profit_margin'])
        tickers.to_csv('items.csv',index=False)
        holding_value = pd.DataFrame(columns = ['holding_value'])
        holding_value.to_csv('returns.csv',index=False)
    
    def config_extract_provided_values(self, args_as_dict):
        
        tikr_values = [[np.NaN, "undef", np.NaN, np.NaN, np.NaN, np.NaN,np.NaN,"undef","undef", "undef", "undef",np.NaN,np.NaN,np.NaN,np.NaN,np.NaN,np.NaN]]
        for argument in  args_as_dict:
           if argument in attr_index_mapping:
              tikr_values[0][attr_index_mapping[argument]] = args_as_dict[argument]
        tikr_values = pd.DataFrame(tikr_values, columns=['ticker', 'currency', 'current_price', 'initial_price', 'holding', 'alert_threshold', 'target_price','sector','industry', 'country','analyst_rating','pb_ratio','pe_ratio','peg_ratio','ev_ebitda_ratio','market_cap_in_ref_currency','profit_margin'])      
        return tikr_values
                    
        
    def config_add_item_list(self, args_as_dict):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir(userhome)
        if not os.path.exists("stockscraper_config") or not os.path.exists("stockscraper_config/items.csv"):
            print('Couldn\'t find settings folder. Please run a config first')
            return
        os.chdir("stockscraper_config")
        tickers = pd.read_csv("items.csv")
        tickers =  pd.concat([self.config_extract_provided_values(args_as_dict), tickers],ignore_index=True)
        tickers.to_csv("items.csv",index=False)

                

                                     
            
    
 
        
        
        

def main():
    config = StockScrapeConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', action="store", required=False, default=None, type=str)
    parser.add_argument('--reference_currency', action="store", required=False, default=None, type=str)
    '''Default values are set to undef, rather than N/A, because if you do, then when pandas 
    reads it in, it will intepret it as NaN, causing incompatability issues'''
    parser.add_argument('--currency', action="store", required=False, default="undef")
    parser.add_argument('--current_price', action="store", required=False, default=np.NAN)
    parser.add_argument('--initial_price', action="store", required=False, default=np.NAN)
    parser.add_argument('--holding', action="store", required=False, default=np.NAN)
    parser.add_argument('--alert_threshold', action="store", required=False, default=np.NAN)
    parser.add_argument('--overwrite', action="store_true", default=False)
    parser.add_argument('--ref_currency', action="store", default=False)
    parser.add_argument('--advanced_webscrape',action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update_items', action="store_true")
    group.add_argument('--additem', action="store_true")
    group.add_argument('--config', action="store_true")
    group.add_argument('--compute_returns',action="store_true")
    group.add_argument('--portfolio_report',action="store_true")
    group.add_argument('--generate_dummy_returns',action="store_true")
    args = parser.parse_args()


    if args.config:
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        if os.path.isfile(f"{userhome}/stockscraper_config/items.csv") and args.overwrite or not os.path.isfile(f"{userhome}\\stockscraper_config\\items.csv"):
            print('Setting up script')
            config.config_setup(args.ref_currency)
            print('Setup complete')
        else:
            print('Config file already found to be present. Run the config with --overwrite to overwrite the existing configuration')
    elif args.additem:
        '''Conditionaly requiring arguments is a tad bit tricky, based on discussions on StackOverflow
        This approach is the dumbest, but the case is so simple that it will do just fine'''
        if args.ticker:           
            config.config_add_item_list(vars(args))
        else:
            print('Errror, provide at least the ticker of the stock')
        '''I would have preferred to only initialize it once at a more outer scope, but initializing
        a StockerScraper object involves reading in a users config, which would fail if they had not
        already run a config setup.'''
    elif args.update_items:
        scraper = StockScraper(args.advanced_webscrape)
        scraper.scraper_update_ticker_info()
    elif args.compute_returns:
        scraper = StockScraper(args.advanced_webscrape)
        scraper.scraper_get_daily_returns()
    elif args.generate_dummy_returns:
        scraper = StockScraper(args.advanced_webscrape)
        scraper.scraper_generate_dummy_returns()
    elif args.portfolio_report:
        profiler = StockProfiler()
        profiler.profiler_generate_report_info()
    
         
            


    
if __name__ == "__main__":
    main()
    