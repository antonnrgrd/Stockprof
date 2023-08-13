import os
import pandas as pd
import datetime
class StockProfiler:
    def __init__(self):
        self.currency_holdings = None
        self.regions = None
        present_date = datetime.datetime.now()
        self.title = present_date.strftime("%d%m%Y")
        self.counter = 1
    def profiler_write_report(self):
        pass
    def profiler_write_preamble(self,latex_report):
        latex_report.write("""\\documentclass{article}
        \\usepackage{tikz}                   
        \\begin{document}
        \\begin{titlepage}
           \\vspace*{\stretch{1.0}}
           \\begin{center}
              \\Large\textbf{My title}\\
              \\large\textit{A. Thor}
           \\end{center}
           \\vspace*{\stretch{2.0}}
        \\end{titlepage}
        """)
        
    def profiler_write_ending(self,latex_report):
         latex_report.write(""""\end{document}""")
    def profiler_generate_report_info(self):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        if os.path.isfile(f"{userhome}\\stockscraper_config\\items.csv"):
            tickers =  pd.read_csv(f"{userhome}\\stockscraper_config\\items.csv")
            currencies = tickers.currency.unique()
            tickers.groupby(['Fruit','Name']).sum()