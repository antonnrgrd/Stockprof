import argparse
from pathlib import Path
import os
import json
import platform
import pandas as pd
import numpy as np
from GEScrape import *
stock_values = ['ticker', 'current_price', 'initial_price', 'holding', 'currency']
class StockScrapeConfig:
    

        
    ''' '''
    def setup_extract_provided_item_info(self,args):
        new_item_info = np.array([None, np.NAN, np.NAN, np.NAN, np.NAN])
        for argument in vars(args):
           if argument in attr_index_mapping:
              new_item_info[argument] = getattr(args, argument)
        return new_item_info
                
    def setup_scraper_script(self):
        os = platform.system()
        if os.lower() == "windows":
            pass
        elif os.lower() == "linux":
            pass
    def config_setup(self, email):
        '''Makes some assumptions that aren't always true. There is no constraint that requires the username to appear in the homedir path on Linux. 
        It just happens to be the case most of the time, but a sysadmin can set a user's homedir to whatever they want '''
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir(userhome)
        if not os.path.exists("stockscraper_config"):
            os.makedirs("stockscraper_config")
        os.chdir("stockscraper_config")
        with open('meta_data.json', 'w') as f:
            json.dump({"email": email, "error_state": False}, f)
        ge_items = pd.DataFrame(columns = ['ticker','currency', 'current_price', 'initial_price', 'holding', 'alert_threshold'])  
        ge_items.to_csv('items.csv')
    
    def config_extract_values(self, args):
        tikr_values = [np.NaN, np.NaN, np.NaN, np.NaN, np.NaN]
        for value in stock_values:
                    
        
    def config_add_item_list(self, new_item_list=None, args = None):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir(userhome)
        if not os.path.exists("stockscraper_config") or not os.path.exists("stockscraper_config/items.csv"):
            print('Couldn\'t find settings folder. Please run a config first')
            return
        os.chdir("stockscraper_config")
        tickers = pd.read_csv("items.csv",index_col=0)
        new_item_info = self.setup_extract_provided_item_info(args)
        tickers[] = new_item_info
        tickers.to_csv()
                

                                     
            
    
 
        
        
        

def main():
    config = GEScrapeConfig()
    scraper = GEScraper()
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', action="store", required=False, default=None, nargs=1)
    parser.add_argument('--ticker', action="store", required=True, default=None, nargs=1)
    parser.add_argument('--currency', action="store", required=True, default=None, nargs=1)
    parser.add_argument('--current_price', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--initial_price', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--holding', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--alert_threshold', action="store", required=False, default=np.NAN, nargs=1)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update_items', action="store_true")
    group.add_argument('--additem', action="store_true")
    group.add_argument('--config', action="store_true")
    args = parser.parse_args()
    if args.config:
        if args.email:
            print('Setting up script')
            config.config_setup(args.email)
            print('Setup complete')
        else:
            print('Error, attempted to config pyexchange without an email')
    elif args.additem:    
        config.config_add_item_list(args.item)
        else:
            print('Errror, provide at least the url and name of the item')
    elif args.update:
        scraper.check_items()
    
         
            


    
if __name__ == "__main__":
    main()
    