import os
import pandas as pd
import datetime
import requests as r
import re
import json
import numpy as np
ex_rate_regex = "(Converted\sto<\/label><div>)([0-9\.+]+)(<)"
class StockProfiler:
    def __init__(self):
        self.conversion_factors = {}
        self.regions = None
        present_date = datetime.datetime.now()
        present_date = present_date.strftime("%d-%m-%Y")
        self.title = f"Portfolio report dated { present_date}"
        self.counter = 1
    def profiler_derive_information(self, tickers,reference_currency):
        currencies = tickers.currency.unique()
        '''We are not interested in the conversion ratio for the reference currency, so we 
        disregard the reference currency, if there is any'''
        currencies = currencies[currencies != reference_currency]
        for currency in currencies:
            conversion_factor_text = r.get(f"https://wise.com/us/currency-converter/{currency}-to-{reference_currency}-rate?amount=1").text
            factor = float(re.search(ex_rate_regex,conversion_factor_text).group(2).replace(",",""))
            self.conversion_factors[currency]=factor

    def profiler_write_report(self):
        pass
    def profiler_write_preamble(self,latex_report):
        latex_report.write("""\\documentclass{article}
        \\usetikzlibrary{positioning,arrows} 
        \\usepackage{tikz}                   
        \\begin{document}
        \\begin{titlepage}
           \\vspace*{\stretch{1.0}}
           \\begin{center}
              \\Large\textbf{Stock portfolio report dated}\\
              \\large\textit{A. Thor}
           \\end{center}
           \\vspace*{\stretch{2.0}}
        \\end{titlepage}
        """)
        
        
    def profiler_write_biggest_earner_loser(self,latex_report):
        latex_report.write("""
        \begin{center}
    \begin{minipage}{.2\textwidth}
    
    \begin{tikzpicture}[scale=0.33] %[x={10.0pt},y={10.0pt}]
    \draw[green,->, ultra thick] (0,0) -- (0,1);
    \end{tikzpicture} % pic 1
    \end{minipage} 
     \begin{minipage}{.2\textwidth}
    
    \begin{tikzpicture}[scale=0.33] %[x={10.0pt},y={10.0pt}]
    
     \draw[red,->, ultra thick] (0,0) -- (0,-1);
    
    \end{tikzpicture}
    
    \end{minipage}
    
    \end{center}                   
        """)
        
    def profiler_write_ending(self,latex_report):
         latex_report.write(""""\end{document}""")
   # @classmethod
    def profiler_generate_report_info(self):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        if os.path.isfile(f"{userhome}\\stockscraper_config\\items.csv"):
            tickers =  pd.read_csv(f"{userhome}\\stockscraper_config\\items.csv")
            with open(f"{userhome}\\stockscraper_config\\config_info.json") as f:
                config_info = json.load(f)
                self.profiler_derive_information(tickers, config_info["ref_currency"])
            tickers['currency_amount'] = tickers.holding * tickers.current_price
            currency_holdings = tickers.groupby(['currency'])['currency_amount'].sum().reset_index()
            '''We convert the target currency to the reference currency e.g DKK. If it is not present in the conversion factors, we assume
            that it is because it is the reference currency and so return it as so.'''
            currency_holdings["own_currency"] = currency_holdings.apply(lambda currencies: currencies["currency_amount"] * self.conversion_factors[currencies["currency"]] if currencies["currency"] in self.conversion_factors else currencies["currency_amount"], axis=1)
            total_holding_own_currency = currency_holdings["own_currency"].sum()
            currency_holdings["weighting"] = currency_holdings["own_currency"] / total_holding_own_currency

    
            sector_holdings = tickers.groupby(['sector','currency'])['currency_amount'].sum().reset_index()
            industry_holdings = tickers.groupby(['industry','currency'])['currency_amount'].sum().reset_index()
            print(industry_holdings)
            
            tickers['returns'] = tickers.initial_price / tickers.current_price
            biggest_return_p =  tickers.loc[tickers['returns'].idxmax()]
            biggest_loss_return_p =  tickers.loc[tickers['returns'].idxmin()]
            