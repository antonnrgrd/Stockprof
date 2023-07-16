import argparse
from pathlib import Path
import os
import json
import platform
import pandas as pd
import numpy as np
from GEScrape import *
attr_index_mapping = {'name' : 0, 'url' : 1 , 'curprice': 2, 'initprice': 3, 'curhold': 4, 'threshold': 5}
class GEScrapeConfig:
    ''' '''
    def setup_extract_provided_item_info(self,args):
        new_item_info = np.array([None, None, np.NAN, np.NAN, np.NAN, np.NAN ])
        for argument in vars(args):
           # print(argument, getattr(args, argument))
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
        if not os.path.exists("gescraper_config"):
            os.makedirs("gescraper_config")
        os.chdir("gescraper_config")
        with open('meta_data.json', 'w') as f:
            json.dump({"email": email, "error_state": False}, f)
        ge_items = pd.DataFrame(columns = ['name', 'url', 'current_price', 'initial_price', 'current_holding', 'alert_threshold'])  
        ge_items.to_csv('items.csv')
        
    def config_add_item_list(self, new_item_list=None, args = None):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        os.chdir(userhome)
        if not os.path.exists("gescraper_config") or not os.path.exists("gescraper_config/items.csv"):
            print('Couldn\'t find settings folder. Please run a config first')
            return
        os.chdir("gescraper_config")
        df = pd.read_csv("items.csv",index_col=0)
        if new_item_list:
            new_item_info = np.array([None, np.NAN, np.NAN, np.NAN, np.NAN ])
            '''If i have not misunderstood the argparse documentation, it does not support at least x argumements,
            only e.g at least one or exactly n arguements, so we have to manually check it here.'''
            if len(new_item_list) < 2:
                print('Error: at least provide a name, followed by a url')
                '''Iterating over the indexes like this is the kids-table equivalent of python list
                processing, but what we are doing is so ad-hoc, off the map of normal list work that it is
                sorta of neccessary, because we are copying parts of a variable-size list to a fixed-length list
                Perhaps at a later date i could atttempt something more clever'''
            for i,value in enumerate(new_item_list[1::]):
                new_item_info[i] = value
            '''Threads on stack overflow point out that it is not unimport how you add rows - some approaches
            are far more heavy than others, but the amount of rows added at a time or so small that i do not expect
            performance to be that important.'''
            df.loc[new_item_list[0]] = new_item_info
            df.to_csv("items.csv")
        else:
            new_item_info = self.setup_extract_provided_item_info(args)
                

                                     
            
    
 
        
        
        

def main():
    config = GEScrapeConfig()
    scraper = GEScraper()
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', action="store", required=False, default=None, nargs=1)

   # parser.add_argument('--item', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--name', action="store", required=False, default=None, nargs=1)
    parser.add_argument('--url', action="store", required=False, default=None, nargs=1)
    parser.add_argument('--curprice', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--initprice', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--curhold', action="store", required=False, default=np.NAN, nargs=1)
    parser.add_argument('--threshold', action="store", required=False, default=np.NAN, nargs=1)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update_items', action="store_true")
    group.add_argument('--additem', action="store_true")
    group.add_argument('--item', action="store", required=False, default=False, nargs="+")
    group.add_argument('--config', action="store_true")
    args = parser.parse_args()
    #config.setup_extract_provided_item_info(args)
    if args.config:
        if args.email:
            print('Setting up script')
            config.config_setup(args.email)
            print('Setup complete')
        else:
            print('Error, attempted to config pyexchange without an email')
    elif args.additem:
        if args.url and args.name or args.item:
            if not args.item:
                pass
            else:           
                config.config_add_item_list(args.item)
        else:
            print('Errror, provide at least the url and name of the item')
    elif args.update:
        scraper.check_items()
    
         
            


    
if __name__ == "__main__":
    main()
    