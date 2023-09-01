import os
import pandas as pd
import datetime
import requests as r
import re
import json
import math
ex_rate_regex = "(Converted\sto<\/label><div>)([0-9\.+]+)(<)"


class StockProfiler:
    def __init__(self):
        counter = 1
        self.reference_currency = None
        self.conversion_factors = {}
        self.regions = None
        present_date = datetime.datetime.now()
        present_date = present_date.strftime("%d-%m-%Y")
        self.title = f"Portfolio_report_dated_{present_date}"
        self.present_date = present_date
        userhome = os.path.expanduser('~') 
        if os.path.exists("{}\\stockscraper_config\\{}.tex".format(userhome, self.title)):
            self.title = f"Portfolio_report_dated_{present_date}({counter})"
            while os.path.exists("{}\\stockscraper_config\\{}.tex".format(userhome, self.title)):
                counter = counter + 1
                self.title = f"Portfolio_report_dated_{present_date}({counter})"
    def profiler_write_distribution_section(self, latex_report):
        latex_report.write("""
                           \\section*{Distribution of holdings}
                           """
            )
                              
    def profiler_write_pchart(self, latex_report, currency_weighting,column,caption, remaining_weighting=None):
        latex_report.write("""
                           \\begin{figure}
                           \\begin{tikzpicture}
                           \\pie{
        """)
        
        '''tikz expect the value in the pie chart to be in the range 0-100, representing the percentage but the way we compute the
        weight it is between 0-1, so we multiply by 100 to ensure it has this property. Furthermore, tikz expect the values to sum abou 100
        or close to, in order to render the pie chart correctly, so we round them up to nudgde it in that direction, at the cost of some accuracy'''
        for index in range (len(currency_weighting)-1):
            latex_report.write("""{} / {}  , """.format(math.ceil(currency_weighting.at[index,'weighting'] * 100) ,currency_weighting.at[index,column] ))
        if remaining_weighting != None:
            latex_report.write("""{} / Other """.format(math.ceil(remaining_weighting * 100)))
        else:
            latex_report.write(""", """)
            latex_report.write("""
                               
                               {} / {} 
                               
                               """.format(currency_weighting.iloc[-1]["weighting"],currency_weighting['currency'].iloc[-1]["currency"] ))
        latex_report.write("""
                        }}
                     \\end{{tikzpicture}}
                     \\caption{{ {} }}
                     \\end{{figure}}
                           """.format(caption))
    def profiler_write_information_section(self, latex_report):
        latex_report. write(""" \\section*{Information used}""")
    def profiler_write_preamble(self, latex_report):
        latex_report.write(
          """
        \\documentclass{article}
        \\usepackage{graphicx} % Required for inserting images
        \\usepackage{tikz}
        \\usepackage{multirow}
        \\usetikzlibrary{positioning,arrows}
        \\usetikzlibrary{arrows.meta}
        \\title{Portfolio report}
        \\usepackage{pgf-pie}  
        \\usepackage{subcaption}
        \\date{Dated """ +  self.present_date + """ } """ 
        +
        
        """
        \\begin{document}
        \\maketitle
        \\tableofcontents   
        """)  
          
           
    def profiler_write_end(self, latex_report):
        latex_report.write("""\\end{document} """)
    def profiler_write_currency_conversion_info(self,latex_report):
        reference_currency = self.reference_currency
        '''We are not interested in writing the conversion factor out for the reference currency, since it is trivially 1 '''
        self.conversion_factors.pop(self.reference_currency, None)
        latex_report.write("""
                           \\subsection*{Conversion factors} """)
        if len(self.conversion_factors) <=5:
            latex_report.write("""\\begin{{table}}[!h]
                                \\begin{{center}}
                                \\begin{{tabular}}{{||c ||}} 
                                 \hline
                                 Reference currency : {}  \\\ [0.5ex] 
                                 \hline\hline
                              """.format(reference_currency))
            for currency, factor in self.conversion_factors.items():
                latex_report.write("""{} : {}  \\\ 
                                   \hline """.format(currency, factor))
        else:
            latex_report.write(
                """
                \\begin{{table}}[!h]
                \\begin{{center}}
                \\begin{{tabular}}{{ |c||c|  }}
                 \\hline
                 \\multicolumn{{2}}{{|c|}}{{ Reference currency : {} }} \\\\
                 \\hline
                 \\hline
                """
                .format(self.reference_currency))
            iterable_factors = iter(self.conversion_factors.items())
            for currency_factor in iterable_factors:
                first_factor, second_factor = currency_factor, next(iterable_factors, None)
                if second_factor != None:
                    latex_report.write("""{} : {} & {} : {}  \\\ 
                                   \hline """.format(first_factor[0], first_factor[1],second_factor[0], second_factor[1]))
                else:
                     latex_report.write("""{} : {} &   \\\ 
                                        
                                   \hline """.format(first_factor[0], first_factor[1]))
        latex_report.write("""
                           \\end{tabular}
                            \\caption{{Conversion factors for reference currency.}}
                            \\end{center}
                            \\end{table}
                           """)
    def profiler_derive_information(self, tickers,reference_currency):
        self.reference_currency = reference_currency
        currencies = tickers.currency.unique()
        '''We are no interested in getting the conversion factor for the reference currency as we know it is 1 '''
        currencies = currencies[currencies != reference_currency]
        for currency in currencies:
            conversion_factor_text = r.get(f"https://wise.com/us/currency-converter/{currency}-to-{reference_currency}-rate?amount=1").text
            factor = float(re.search(ex_rate_regex,conversion_factor_text).group(2).replace(",",""))
            self.conversion_factors[currency]=factor
        '''We have the conversion factor of the reference currency, since it allow us to skimp on a lot of logic
        when converting the currencies to the reference currency'''
        self.conversion_factors[reference_currency] = 1
    def profiler_get_as_ref_currency(self, stock_info):
        if stock_info["currency"] in self.conversion_factors:
            return stock_info["currency_amount"] * self.conversion_factors[stock_info["currency"]]
        else:
            return stock_info["currency_amount"]
    def profiler_write_report(self):
        pass
        
        
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
         latex_report.write("""\end{document}""")
   # @classmethod
    def profiler_generate_report_info(self):
        userhome = os.path.expanduser('~')          
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
            sector_holdings["currency_amount"] = sector_holdings["currency"].map(self.conversion_factors).mul(sector_holdings["currency_amount"]) 
            sector_holdings = sector_holdings.rename(columns={'currency_amount': 'own_currency'})
            sector_weighting = sector_holdings.groupby(['sector'])['own_currency'].sum().reset_index()
            sector_weighting["weighting"] = sector_weighting["own_currency"] / total_holding_own_currency

            


            
            industry_holdings = tickers.groupby(['industry','currency'])['currency_amount'].sum().reset_index()
            industry_holdings["currency_amount"] = industry_holdings["currency"].map(self.conversion_factors).mul(industry_holdings["currency_amount"]) 
            industry_holdings = industry_holdings.rename(columns={'currency_amount': 'own_currency'})
            industry_weighting = industry_holdings.groupby(['industry'])['own_currency'].sum().reset_index()
            industry_weighting["weighting"] = industry_weighting["own_currency"] / total_holding_own_currency

            country_holdings = tickers.groupby(['country','currency'])['currency_amount'].sum().reset_index()
            country_holdings["currency_amount"] = country_holdings["currency"].map(self.conversion_factors).mul(country_holdings["currency_amount"]) 
            country_holdings = country_holdings.rename(columns={'currency_amount': 'own_currency'})
            country_weighting = country_holdings.groupby(['country'])['own_currency'].sum().reset_index()
            
            tickers['returns'] = tickers.initial_price / tickers.current_price
            biggest_return_p =  tickers.loc[tickers['returns'].idxmax()]
            biggest_loss_return_p =  tickers.loc[tickers['returns'].idxmin()]
            
            

            
            userhome = os.path.expanduser('~') 
            with open("{}\\stockscraper_config\\{}.tex".format(userhome, self.title), 'w') as report:
                self.profiler_write_preamble(report)
                self.profiler_write_distribution_section(report)
                if len(currency_holdings) > 5:
                    biggest_currency_holdings = currency_holdings.nlargest(5, columns=['weighting']).reset_index()
                    remaining_weight = 1 - biggest_currency_holdings['weighting'].sum()
                    self.profiler_write_pchart(report, biggest_currency_holdings,"currency", "Distribution of currencies", remaining_weight)
                else:
                    self.profiler_write_pchart(report, currency_holdings,"currency","Distribution of currencies")
                self.profiler_write_information_section(report)
                self.profiler_write_currency_conversion_info(report)
                self.profiler_write_ending(report)
                 


                     