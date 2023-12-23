from sklearn import tree
class StockAnalyser:
    def __init__(self):
        self.num_rating_to_str_rating = {}
        self.decision_tree = None
    def stock_analyzer_train_model(self,tickers,analyst_ratings):
        tickers = tickers.loc[:, tickers.columns != "analyst_rating"]
        self.decision_tree.fit(tickers, analyst_ratings)
    def stock_analyzer_predict(self,ticker):
        return  self.stock_analyser_map_num_rating_to_str_rating(self.decision_tree.predict(ticker))
    '''While the stocks have a discrete rating e.g Strong buy, buy, hold etc.
    they also have related  fuzzyness to them e.g '''
    def stock_analyser_map_float_to_int(self, rating):
        if rating <=2:
            return 1
        elif rating <=3:
            return 2
        elif rating <=4:
            return 3
        elif rating <=5:
            return 4
        else:
            return 5
    def stock_analyser_map_num_rating_to_str_rating(self, rating):
        if rating <=2:
            return ("Strong buy", rating)
        elif rating <=3:
            return ("Buy", rating)
        elif rating <=4:
            return ("Hold", rating)
        elif rating <=5:
            return ("Underperform", rating)
        else:
            return ("Sell", rating)
        