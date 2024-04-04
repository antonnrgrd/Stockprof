from sklearn import tree
from sklearn import model_selection
import numpy as np
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
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
    def stock_analyser_fit_returns_function(self, dates_as_offsets, holding_values):
        best_r2= -np.inf
        best_model = None
        svr_rbf = SVR(kernel="rbf", C=100, gamma=0.1, epsilon=0.1)
        svr_lin = SVR(kernel="linear", C=100, gamma="auto")
        svr_poly = SVR(kernel="poly", C=100, gamma="auto", degree=3, epsilon=0.1, coef0=1)
        regression_models = [svr_rbf,svr_lin,svr_poly]
        for regression_model in regression_models:
            X_train, X_test, y_train, y_test = model_selection(dates_as_offsets, holding_values, shuffle=True, train_size=0.3)
            regression_model.fit(X_train, y_train)
            predictions = regression_model.predict(X_test)
            r2 = r2_score(y_test, predictions)
            if r2 > best_r2:
                best_r2 = r2
                best_model = regression_model
        return (best_model, best_r2)


        