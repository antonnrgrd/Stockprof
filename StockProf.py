import os
import pandas as pd
import datetime
import requests as r
import re
import json
import math
from StockScraper import *
ex_rate_regex = "(Converted\sto<\/label><div>)([0-9\.+]+)(<)"


class StockProfiler:
    def __init__(self):
        self.scraper = StockScraper()
        counter = 1
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
    def profiler_write_returns(self, latex_report, returns, time_frame):
        latex_report.write
    
    def profiler_write_returns_monthly(self, returns):
        previous_monthly_returns = returns.iloc[0:30]
    def profiler_write_returns_yearly(self):
        pass
    def profiler_write_returns_five_yearly(self):
        pass
    def profiler_sanitize_ticker_data(self, tickers):
        '''These values are present in various values in the dataframe. They give issues with rendering the reports
        so we will rehave to replace them with something it can render'''
        tickers["industry"] = tickers['industry'].str.replace('&', '\&')
        tickers["industry"] = tickers['industry'].str.replace('—', '-')

    def profiler_write_section_type(self,latex_report, title, section_type, footnote=""):
        if section_type == "section":
            latex_report.write("""
                           \\section*{{{title}}}
                           """.format(title=title) + footnote
            )
        elif section_type == "subsection":
            latex_report.write("""
                           \\subsection*{{{title}}}
                           """.format(title=title) + footnote
            )
        elif section_type == "subsubsection":
           latex_report.write("""
                           \\subsubsection*{{{title}}}
                           """.format(title=title) + footnote
            )
        else:
            raise Exception("Undefined section type")
        


            
    
   
    def profiler_write_tikz_begin(self, latex_report, optional_info=None):
        if optional_info != None:
            latex_report.write("""
                           \\begin{tikzpicture}""" + optional_info)
        else:
            latex_report.write("""
                           \\begin{tikzpicture}""")
                
            
        
                           
    def profiler_write_tikz_end(self, latex_report):
         latex_report.write("""
                          \\end{tikzpicture}""")
    def profiler_write_pchart(self, latex_report, currency_weighting,column,radius, x_pos, y_pos, remaining_weighting=None):
        latex_report.write("""
                           \\pie[radius={radius}, pos= {{{x_pos},{y_pos}}}]{{
        """.format(radius=radius, x_pos= x_pos, y_pos = y_pos))
        
        '''tikz expect the value in the pie chart to be in the range 0-100, representing the percentage but the way we compute the
        weight it is between 0-1, so we multiply by 100 to ensure it has this property. Furthermore, tikz expect the values to sum abou 100
        or close to, in order to render the pie chart correctly, so we round them up to nudgde it in that direction, at the cost of some accuracy'''
        for index in range (len(currency_weighting)-1):
            latex_report.write("""{fraction} / {value}  , """.format(fraction=math.ceil(currency_weighting.at[index,'weighting'] * 100) ,value=currency_weighting.at[index,column] ))
        if remaining_weighting != None:
            latex_report.write("""{fraction} / Other """.format(fraction=math.ceil(remaining_weighting * 100)))
        else:
            latex_report.write(""", """)
            latex_report.write("""
                               
                               {} / {} 
                               
                               """.format(currency_weighting.iloc[-1]["weighting"],currency_weighting[column].iloc[-1][column] ))
        latex_report.write(""" 
                           }
                           """)
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
        \\usetikzlibrary {datavisualization} 
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
        reference_currency = self.scraper.reference_currency
        '''We are not interested in writing the conversion factor out for the reference currency, since it is trivially 1 '''
        self.scraper.conversion_factors.pop(self.scraper.reference_currency, None)
        latex_report.write("""
                           \\subsection*{Conversion factors} """)
        if len(self.scraper.conversion_factors) <=5:
            latex_report.write("""\\begin{{table}}[!h]
                                \\begin{{center}}
                                \\begin{{tabular}}{{||c ||}} 
                                 \hline
                                 Reference currency : {}  \\\ [0.5ex] 
                                 \hline\hline
                              """.format(reference_currency))
            for currency, factor in self.scraper.conversion_factors.items():
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
                .format(self.scraper.reference_currency))
            iterable_factors = iter(self.scraper.conversion_factors.items())
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

    def profiler_get_as_ref_currency(self, stock_info):
        if stock_info["currency"] in self.scraper.conversion_factors:
            return stock_info["currency_amount"] * self.scraper.conversion_factors[stock_info["currency"]]
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
    def profiler_write_enumerate(self, latex_report, ):
        pass
    def profiler_generate_report_info(self):
        userhome = os.path.expanduser('~')          
        if os.path.isfile(f"{userhome}\\stockscraper_config\\items.csv"):
            tickers =  pd.read_csv(f"{userhome}\\stockscraper_config\\items.csv")
            self.scraper.scraper_get_currency_conv_factors(tickers)
            self.profiler_sanitize_ticker_data(tickers)
            tickers['currency_amount'] = tickers.holding * tickers.current_price
            currency_holdings = tickers.groupby(['currency'])['currency_amount'].sum().reset_index()
            '''We convert the target currency to the reference currency e.g DKK. If it is not present in the conversion factors, we assume
            that it is because it is the reference currency and so return it as so.'''
            currency_holdings["own_currency"] = currency_holdings.apply(lambda currencies: currencies["currency_amount"] * self.scraper.conversion_factors[currencies["currency"]] if currencies["currency"] in self.scraper.conversion_factors else currencies["currency_amount"], axis=1)
            total_holding_own_currency = currency_holdings["own_currency"].sum()
            currency_holdings["weighting"] = currency_holdings["own_currency"] / total_holding_own_currency

    
            sector_holdings = tickers.groupby(['sector','currency'])['currency_amount'].sum().reset_index()
            sector_holdings["currency_amount"] = sector_holdings["currency"].map(self.scraper.conversion_factors).mul(sector_holdings["currency_amount"]) 
            sector_holdings = sector_holdings.rename(columns={'currency_amount': 'own_currency'})
            sector_weighting = sector_holdings.groupby(['sector'])['own_currency'].sum().reset_index()
            sector_weighting["weighting"] = sector_weighting["own_currency"] / total_holding_own_currency

            


            
            industry_holdings = tickers.groupby(['industry','currency'])['currency_amount'].sum().reset_index()
            industry_holdings["currency_amount"] = industry_holdings["currency"].map(self.scraper.conversion_factors).mul(industry_holdings["currency_amount"]) 
            industry_holdings = industry_holdings.rename(columns={'currency_amount': 'own_currency'})
            industry_weighting = industry_holdings.groupby(['industry'])['own_currency'].sum().reset_index()
            industry_weighting["weighting"] = industry_weighting["own_currency"] / total_holding_own_currency

            country_holdings = tickers.groupby(['country','currency'])['currency_amount'].sum().reset_index()
            country_holdings["currency_amount"] = country_holdings["currency"].map(self.scraper.conversion_factors).mul(country_holdings["currency_amount"]) 
            country_holdings = country_holdings.rename(columns={'currency_amount': 'own_currency'})
            country_weighting = country_holdings.groupby(['country'])['own_currency'].sum().reset_index()
            country_weighting["weighting"] = country_weighting["own_currency"] / total_holding_own_currency
            
            tickers['returns'] = tickers.initial_price / tickers.current_price
            biggest_return_p =  tickers.loc[tickers['returns'].idxmax()]
            biggest_loss_return_p =  tickers.loc[tickers['returns'].idxmin()]
            
            

            
            userhome = os.path.expanduser('~') 
            with open("{}\\stockscraper_config\\{}.tex".format(userhome, self.title), 'w') as report:
                self.profiler_write_preamble(report)
                self.profiler_write_section_type(report, "Distribution of holdings", "section")
                self.profiler_write_section_type(report, "Distribution of currencies and countries", "subsection")
                self.profiler_write_tikz_begin(report,"""[auto=left] 
\\node[circle] at (-3,-3) {Distribution of currencies in holdings};
\\node[circle] at (4,-3) {Distribution of nationality in holdings};""")
                if len(currency_holdings) > 5:
                    biggest_currency_holdings = currency_holdings.nlargest(5, columns=['weighting']).reset_index()
                    remaining_weight = 1 - biggest_currency_holdings['weighting'].sum()
                    self.profiler_write_pchart(report, biggest_currency_holdings,"currency",2, -3, 0, remaining_weight)
                else:
                    self.profiler_write_pchart(report, currency_holdings,"currency",2, -3, 0)
                if len(country_holdings) > 5:
                     biggest_country_holdings = country_weighting.nlargest(5, columns=['weighting']).reset_index()
                     remaining_weight = 1 - biggest_country_holdings['weighting'].sum()
                     self.profiler_write_pchart(report, biggest_country_holdings,"country",2, 4, 0, remaining_weight)
                else:
                    self.profiler_write_pchart(report, biggest_country_holdings,"country",2, 4, 0)
                self.profiler_write_tikz_end(report)
                self.profiler_write_section_type(report, "Distribution of sectors and industries", "subsection")
                
                self.profiler_write_tikz_begin(report,"""[auto=left] 
\\node[circle] at (-3,-3) {Distribution of sector in holdings};
\\node[circle] at (4,-3) {Distribution of industry in holdings};""")
                if len(sector_holdings) > 5:
                    biggest_sector_holdings = sector_weighting.nlargest(5, columns=['weighting']).reset_index()
                    remaining_weight = 1 - biggest_sector_holdings['weighting'].sum()
                    self.profiler_write_pchart(report, biggest_sector_holdings,"sector",2, -3, 0, remaining_weight)
                else:
                    self.profiler_write_pchart(report, currency_holdings,"currency",2, -3, 0)
                if len(industry_holdings) > 5:
                     biggest_industry_holdings = industry_weighting.nlargest(5, columns=['weighting']).reset_index()
                     remaining_weight = 1 - biggest_country_holdings['weighting'].sum()
                     self.profiler_write_pchart(report, biggest_industry_holdings,"industry",2, 4, 0, remaining_weight)
                else:
                    self.profiler_write_pchart(report, biggest_industry_holdings,"country",2, 4, 0)
                self.profiler_write_tikz_end(report)
                self.profiler_write_section_type(report, "Top stocks by weighting", "subsection")   
                
                self.profiler_write_section_type(report, "Information used to produce report", "section")
                self.profiler_write_section_type(report, "Currency conversion rates", "subsection")                
                self.profiler_write_currency_conversion_info(report)
                self.profiler_write_ending(report)
                 


                     