import argparse
from pathlib import Path
import os
import json
import platform
import pandas as pd
import numpy as np
from StockScraper import *
import sys
attr_index_mapping = {'ticker':0,'currency':1, 'current_price':2, 'initial_price':3, 'holding':4,'alert_threshold':5}
class StockScrapeConfig:
    

        


                
    def setup_scraper_script(self):
        os = platform.system()
        if os.lower() == "windows":
            pass
        elif os.lower() == "linux":
            pass
    def config_setup(self, email,password,recipients):
        '''Makes some assumptions that aren't always true. There is no constraint that requires the username to appear in the homedir path on Linux. 
        It just happens to be the case most of the time, but a sysadmin can set a user's homedir to whatever they want '''
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir(userhome)
        if not os.path.exists("stockscraper_config"):
            os.makedirs("stockscraper_config")
        os.chdir("stockscraper_config")
        with open('meta_data.json', 'w') as f:
            json.dump({"email": email, "password":password, "error_state": False},f)
        tickers = pd.DataFrame(columns = ['ticker','currency', 'current_price', 'initial_price', 'holding', 'alert_threshold'])
        tickers.to_csv('items.csv')
    
    def config_extract_provided_values(self, args_as_dict):
        
        tikr_values = [[np.NaN, "undef", np.NaN, np.NaN, np.NaN, np.NaN]]
        for argument in  args_as_dict:
           if argument in attr_index_mapping:
              tikr_values[0][attr_index_mapping[argument]] = args_as_dict[argument]
        tikr_values = pd.DataFrame(tikr_values, columns=['ticker', 'currency', 'current_price', 'initial_price', 'holding', 'alert_threshold'])      
        return tikr_values
                    
        
    def config_add_item_list(self, args_as_dict):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir(userhome)
        if not os.path.exists("stockscraper_config") or not os.path.exists("stockscraper_config/items.csv"):
            print('Couldn\'t find settings folder. Please run a config first')
            return
        os.chdir("stockscraper_config")
        tickers = pd.read_csv("items.csv",index_col=0)
        self.config_extract_provided_values(args_as_dict)
        tickers =  pd.concat([self.config_extract_provided_values(args_as_dict), tickers],ignore_index=True)
        '''Important sitenote, we want to include the integer indexes as a column due to how we iterate over the rows when scraping information
        so we do not set it to false here'''
        print(tickers)
        tickers.to_csv("items.csv")
                

                                     
            
    
 
        
        
        

def main():
    config = StockScrapeConfig()
    scraper = StockScraper()
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', action="store", required=False, default=None, nargs=1)
    parser.add_argument('--password', action="store", required=False, default=None)
    parser.add_argument('--recipients', action="store", required=False, default=None)
    parser.add_argument('--ticker', action="store", required=False, default=None, type=str)
    '''Default values are set to undef, rather than N/A, because if you do, then when pandas 
    reads it in, it will intepret it as NaN, causing incompatability issues'''
    parser.add_argument('--currency', action="store", required=False, default="undef")
    parser.add_argument('--current_price', action="store", required=False, default=np.NAN)
    parser.add_argument('--initial_price', action="store", required=False, default=np.NAN)
    parser.add_argument('--holding', action="store", required=False, default=np.NAN)
    parser.add_argument('--alert_threshold', action="store", required=False, default=np.NAN)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update_items', action="store_true")
    group.add_argument('--additem', action="store_true")
    group.add_argument('--config', action="store_true")
    args = parser.parse_args()
    if args.config:
        if args.email:
            print('Setting up script')
            config.config_setup(args.email,args.password,args.recipients)
            print('Setup complete')
        else:
            print('Error, attempted to config pyexchange without an email')
    elif args.additem:
        '''Conditionaly requiring arguments is a tad bit tricky, based on discussions on StackOverflow
        This approach is the dumbest, but the case is so simple that it will do just fine'''
        if args.ticker:           
            config.config_add_item_list(vars(args))
        else:
            print('Errror, provide at least the ticker of the stock')
    elif args.update_items:
        scraper.check_items()
    
         
            


    
if __name__ == "__main__":
    main()
    