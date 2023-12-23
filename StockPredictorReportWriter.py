import StockPredictor
class StockPredictorReportWriter:
    def __init__(self):
        self.rating_predictor = StockPredictor()
    def stock_predictor_report_writer_write_preamble(self,latex_report):
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
        \\date{Dated """ +  self.present_date + """ } """)
    def stock_predictor_report_writer_prediction(self,latex_report, ticker):
        rating = self.rating_predictor.stock_analyzer_predict(ticker)
        if rating != ticker["analyst_rating"]:
            latex_report.write("""
                               The rating given by StockProf differs from that of the rating given by the analysts, it has given it a rating of {rating},
                               whereas the rating given by the analysts is {analyst_rating}
                               """)
        else:
            latex_report.write("""
                               The rating given by StockProf is {rating}. This is consistent with what is given by the analysts
                               """)
        latex_report.write("""
                           The rating given by StockProf differs from that of the rating given by the analysts, it has given it a rating of {rating},
                           whereas the rating given by the analysts is {analyst_rating}
                           """)  
         