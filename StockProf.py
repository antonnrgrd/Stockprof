import os
import pandas as pd
import datetime
import requests as r
import re
import json
import math
from StockScraper import *
ex_rate_regex = "(Converted\sto<\/label><div>)([0-9\.+]+)(<)"
one_month_tickinfo_regex = "^07-|^14-|^21-|^01|^01-01"
six_months_tickinfo_regex = "^14-|^01|^01-01"
yearly_tickinfo_regex = "^01-|^01-01"
five_years_tickinfo_regex = "^01-01-|^01-06"
class StockProfiler:
    def __init__(self):
        self.scraper = StockScraper()
        counter = 1
        present_date = datetime.datetime.now()
        present_date = present_date.strftime("%d-%m-%Y")
        self.title = f"Portfolio_report_dated_{present_date}"
        self.present_date = present_date
        self.userhome = os.path.expanduser('~') 
        if os.path.exists("{}\\stockscraper_config\\{}.tex".format( self.userhome, self.title)):
            self.title = f"Portfolio_report_dated_{present_date}({counter})"
            while os.path.exists("{}\\stockscraper_config\\{}.tex".format(self.userhome, self.title)):
                counter = counter + 1
                self.title = f"Portfolio_report_dated_{present_date}({counter})"
        self.month_num_to_month_name_mapping = {"01": "Jan.", "02": "Feb.", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July","08":"Aug.","09":"Sept.", "10":"Oct.", "11":"Nov.", "12": "Dec."}
        self.range_to_title_mapping = {"monthly":"{Returns on investment over a one month period}", "six_monthly":"{Returns on investment over a six-month period}","yearly": "{Returns on investment over a year}","five_yearly":"{Returns on investment over five years}"}
   
          
    def profiler_write_axis_information(self, latex_report, returns, time_frame):
        ticks_as_str = "{"
        ticker_values = []
        ticker_labels = []
        tick_labels_as_str = "{"
        if time_frame == "monthly":
            returns_values = returns[returns.index.str.contains(one_month_tickinfo_regex,regex=True)]
            ticker_values = returns_values['index_as_offset'].to_list()
            ticker_dates = returns_values.index.to_list()
            ticker_labels = [self.month_num_to_month_name_mapping[date[3:5]] if date[0:2] == "01" else date[0:2] for date in ticker_dates]
        elif time_frame == "six_monthly":
             returns_values = returns[returns.index.str.contains(six_months_tickinfo_regex,regex=True)]
             ticker_values = returns_values['index_as_offset'].to_list()
             ticker_dates = returns_values.index.to_list()
             ticker_labels = [self.month_num_to_month_name_mapping[date[3:5]] if date[0:2] == "01" else date[0:2] for date in ticker_dates]
        elif time_frame == "yearly":
             returns_values = returns[returns.index.str.contains(yearly_tickinfo_regex ,regex=True)]
             ticker_values = returns_values['index_as_offset'].to_list()
             ticker_dates = returns_values.index.to_list()
             ticker_labels = [date[6:] if date[0:5] == "01-01" else self.month_num_to_month_name_mapping[date[3:5]] for date in ticker_dates]
        elif time_frame == "five_yearly":
            returns_values = returns[returns.index.str.contains(five_years_tickinfo_regex,regex=True)]
            ticker_values = returns_values['index_as_offset'].to_list()
            ticker_dates = returns_values.index.to_list()
            ticker_labels = [date[6:] if date[0:5] == "01-01" else "Jul." for date in ticker_dates]
        '''By how pandas adds values and how the return values are stored in the frame, we have to reverse
        them s.t they are now from biggest value to smallest, to get the correct ticker-label values'''
        ticker_values.reverse()
        ticker_labels.reverse()
        for ticker_value, ticker_label in zip(ticker_values[:-1],ticker_labels[:-1]):
            ticks_as_str = ticks_as_str + f"{ticker_value},"
            tick_labels_as_str =  tick_labels_as_str + f"{ticker_label},"
        ticks_as_str = ticks_as_str + "{last_ticker_value}".format(last_ticker_value=ticker_values[-1])
        tick_labels_as_str =  tick_labels_as_str + "{last_ticker_label_value}".format(last_ticker_label_value=ticker_labels[-1])
        ticks_as_str  = ticks_as_str   + "}"
        tick_labels_as_str = tick_labels_as_str + "}"
        title = self.range_to_title_mapping[time_frame]
        latex_report.write(f"""
                           title={title},
                           xtick={ticks_as_str},
                           xticklabels={tick_labels_as_str},""")
        xtra_ticks = "{"
        for i in range(1,len(returns)):
            xtra_ticks = xtra_ticks + f"{i},"
        xtra_ticks = xtra_ticks + "{last_tick}".format(last_tick = len(returns) )
        xtra_ticks =  xtra_ticks + "}"
        y_tick_values = [round(math.ceil(min(returns["holding_value"])), -1),round(math.ceil(min(returns["holding_value"] * 1.1)), -1),round(math.ceil(min(returns["holding_value"] * 1.2)), -1),round(math.ceil(min(returns["holding_value"] * 1.3)), -1),round(math.ceil(min(returns["holding_value"] * 1.4)), -1),round(math.ceil(min(returns["holding_value"] * 1.5)), -1),round(math.ceil(min(returns["holding_value"] * 1.6)), -1),round(math.ceil(min(returns["holding_value"] * 1.7)), -1),round(math.ceil(min(returns["holding_value"] * 1.8)), -1)]
       # latex_report.write("""ymin={minimum},
       #                    """.format(minimum=min(returns["holding_value"])))
       # latex_report.write("""ymax={maximum},""".format(maximum=max(returns["holding_value"])))
        y_ticks_as_str = "{"
        for y_tick in y_tick_values:
            y_ticks_as_str = y_ticks_as_str + f"{y_tick},"
        y_ticks_as_str = y_ticks_as_str + "{last_value}".format(last_value=round(math.ceil(min(returns["holding_value"] * 1.9)), -1))
        y_ticks_as_str = y_ticks_as_str + "}"
        latex_report.write("""
                          ylabel=Value of holding in {ref_currency},
                          xlabel=Time,""".format(ref_currency=self.scraper.reference_currency))
        '''If the time frame is greater than a monthly period, the number of ticks become too many to
        fit on the axis horizontally, so we have to write them vertically. We also have to move the x-axis
        label a bit further down to avoid overap with the tick labels'''
        if time_frame != "monthly":
             latex_report.write("""
                                tick label style={rotate=90},
                                 x label style={at={(axis description cs:0.5,-0.1)},anchor=north}""")
                                        
    def profiler_write_axis_begin(self,latex_report):
        latex_report.write("""
                           \\begin{axis}[""")
    def profiler_write_axis_mid(self,latex_report):
        latex_report.write("""
                           ]
                          """)                      
    def profiler_write_axis_end(self,latex_report):
        latex_report.write("""
                           \\end{axis}""")
    def profiler_write_monthly_returns_axis(self,latex_report, returns):
        latex_report.write("""
                           title={Returns on investment over a one month period},                 
                           grid = both,
            """)
        self.profiler_write_axis_information(latex_report, returns, "monthly")
    def profiler_write_yearly_returns_axis(self,latex_report, returns):
       latex_report.write("""
                          title={Returns on investment over a yearly period},                 
                          grid = both,
           """)
       self.profiler_write_axis_information(latex_report, returns, "yearly")
    def profiler_write_five_yearly_returns_axis(self,latex_report, returns):
      latex_report.write("""
                         title={Returns on investment over a yearly period},                 
                         grid = both,
          """)
    def profiler_write_returns_period(self, latex_report, returns, timeframe):
        returns_range = None
        if timeframe == "monthly":
            returns_range = returns.iloc[0:30]
        elif timeframe == "six_monthly":
            returns_range = returns.iloc[0:180]
        elif timeframe == "yearly":
            returns_range = returns.iloc[0:365:]
        elif timeframe == "five_yearly":
            returns_range = returns.iloc[0:1825:]
        '''In order to identify the tick values for the axis information, we need to be able to quickly get the associated
        integer "index" of the index. I have tried seeing if there is neat method for doing this, but approach was found. The solution
        was to literally store the values as a column. As a side note, loc returns a REFERENCE i.e shallow copy subset of the
        dataframe and you cannot modify it. We therefore need to have the result of iloc as a seperate copy'''
        returns_range = returns_range.copy()
        returns_range["index_as_offset"] = [x for x in range(len(returns_range),0,-1)]       
        self.profiler_write_tikz_begin(latex_report)
        self.profiler_write_axis_begin(latex_report)
        if timeframe == "monthly":
            self.profiler_write_axis_information(latex_report, returns_range, "monthly")
        elif timeframe == "six_monthly":
            self.profiler_write_axis_information(latex_report, returns_range, "six_monthly")
        elif timeframe == "yearly":
            self.profiler_write_axis_information(latex_report, returns_range, "yearly")
        elif timeframe == "five_yearly":
            self.profiler_write_axis_information(latex_report, returns_range, "five_yearly")
        self.profiler_write_axis_mid(latex_report)
        latex_report.write("""\\addplot [color=red] coordinates {""")
        for i in range(len(returns_range)-1):
            latex_report.write("""({index},{value})
                               """.format(index = i+1,value=returns_range.iloc[i]["holding_value"]))
        latex_report.write("""({index},{value})""".format(index = len(returns_range),value=returns_range.iloc[len(returns_range)-1]["holding_value"]))
        latex_report.write("""
                           };""")

        self.profiler_write_axis_end(latex_report)
        self.profiler_write_tikz_end(latex_report)
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
            latex_report.write("""{fraction} / {value}  , 
                               """.format(fraction=math.ceil(currency_weighting.at[index,'weighting'] * 100) ,value=currency_weighting.at[index,column] ))
        if remaining_weighting != None:
            latex_report.write("""{fraction} / Other """.format(fraction=math.ceil(remaining_weighting * 100)))
        else:
            latex_report.write("""{} / {}""".format(currency_weighting.iloc[-1]["weighting"],currency_weighting.iloc[-1][column] ))
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
        \\usepackage{pgfplots}
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
    
    def profiler_write_weighting_information(self, latex_report, tickers):
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
        
        self.profiler_write_section_type(latex_report, "Distribution of holdings", "section")
        self.profiler_write_section_type(latex_report, "Distribution of currencies and countries", "subsection")
        self.profiler_write_tikz_begin(latex_report,"""[auto=left] 
        \\node[circle] at (-3,-3) {Distribution of currencies in holdings};
        \\node[circle] at (4,-3) {Distribution of nationality in holdings};""")
        if len(currency_holdings) > 5:
            biggest_currency_holdings = currency_holdings.nlargest(5, columns=['weighting']).reset_index()
            remaining_weight = 1 - biggest_currency_holdings['weighting'].sum()
            self.profiler_write_pchart(latex_report, biggest_currency_holdings,"currency",2, -3, 0, remaining_weight)
        else:
            self.profiler_write_pchart(latex_report, currency_holdings,"currency",2, -3, 0)
        if len(country_holdings) > 5:
             biggest_country_holdings = country_weighting.nlargest(5, columns=['weighting']).reset_index()
             remaining_weight = 1 - biggest_country_holdings['weighting'].sum()
             self.profiler_write_pchart(latex_report, biggest_country_holdings,"country",2, 4, 0, remaining_weight)
        else:
            self.profiler_write_pchart(latex_report, country_weighting,"country",2, 4, 0)
        self.profiler_write_tikz_end(latex_report)
        self.profiler_write_section_type(latex_report, "Distribution of sectors and industries", "subsection")
        
        self.profiler_write_tikz_begin(latex_report,"""[auto=left] 
\\node[circle] at (-3,-3) {Distribution of sector in holdings};
\\node[circle] at (4,-3) {Distribution of industry in holdings};""")
        if len(sector_holdings) > 5:
            biggest_sector_holdings = sector_weighting.nlargest(5, columns=['weighting']).reset_index()
            remaining_weight = 1 - biggest_sector_holdings['weighting'].sum()
            self.profiler_write_pchart(latex_report, biggest_sector_holdings,"sector",2, -3, 0, remaining_weight)
        else:
            self.profiler_write_pchart(latex_report, sector_weighting,"sector",2, -3, 0)
        if len(industry_holdings) > 5:
             biggest_industry_holdings = industry_weighting.nlargest(5, columns=['weighting']).reset_index()
             remaining_weight = 1 - biggest_country_holdings['weighting'].sum()
             self.profiler_write_pchart(latex_report, biggest_industry_holdings,"industry",2, 4, 0, remaining_weight)
        else:
            self.profiler_write_pchart(latex_report, industry_weighting,"industry",2, 4, 0)
        self.profiler_write_tikz_end(latex_report)
        self.profiler_write_section_type(latex_report, "Top stocks by weighting", "subsection")   
   

    def profiler_write_performance_information(self, latex_report):
        returns = pd.read_csv("{userhome}/stockscraper_config/returns.csv".format(userhome=self.userhome),index_col=0)
        self.profiler_write_section_type(latex_report, "Portfolio performance", "section")
        self.profiler_write_section_type(latex_report, "Returns", "subsection")
        self.profiler_write_section_type(latex_report, "Monthly returns", "subsubsection")
        self.profiler_write_returns_period(latex_report, returns, "monthly")
        self.profiler_write_section_type(latex_report, "Six monthly returns", "subsubsection")
        self.profiler_write_returns_period(latex_report, returns, "six_monthly")
        self.profiler_write_section_type(latex_report, "Yearly returns", "subsubsection")
        self.profiler_write_returns_period(latex_report, returns, "yearly") 
        self.profiler_write_section_type(latex_report, "Five years returns", "subsubsection")
        self.profiler_write_returns_period(latex_report, returns, "five_yearly") 
    def profiler_generate_report_info(self):
        userhome = os.path.expanduser('~')          
        if os.path.isfile(f"{userhome}\\stockscraper_config\\items.csv"):
            tickers =  pd.read_csv(f"{userhome}\\stockscraper_config\\items.csv")
            self.scraper.scraper_get_currency_conv_factors(tickers)
            self.profiler_sanitize_ticker_data(tickers)
            tickers['returns'] = tickers.initial_price / tickers.current_price
            biggest_return_p =  tickers.loc[tickers['returns'].idxmax()]
            biggest_loss_return_p =  tickers.loc[tickers['returns'].idxmin()]
            
            

            
            userhome = os.path.expanduser('~') 
            with open("{}\\stockscraper_config\\{}.tex".format(userhome, self.title), 'w') as report:
                self.profiler_write_preamble(report)
               
                self.profiler_write_performance_information(report)
                self.profiler_write_weighting_information(report, tickers)
                self.profiler_write_section_type(report, "Information used to produce report", "section")
                self.profiler_write_section_type(report, "Currency conversion rates", "subsection")                
                self.profiler_write_currency_conversion_info(report)
                self.profiler_write_ending(report)
                 


                     