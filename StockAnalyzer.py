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
    they also have related  fuzzyness to them e.g how strong a buy, sell hold rating they have. '''

        