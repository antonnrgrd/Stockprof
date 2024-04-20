from sklearn import tree
from sklearn import model_selection
import numpy as np
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from StockScraper import StockScraper
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder
import os
import pickle
import pandas as pd
class StockAnalyzer:
    def __init__(self, autotrain_model=False,use_portfolio_for_training=False):
        self.enc = OneHotEncoder(handle_unknown='error')
        self.use_portfolio_for_training = use_portfolio_for_training
        self.training_data = None
        self.userhome = os.path.expanduser('~') 
        self.num_rating_to_str_rating = {}
        if os.path.isfile(f"{self.userhome}/stockscraper_config/random_forest_model"):
            self.random_forest = pickle.load(f"{self.userhome}/stockscraper_config/random_forest_model")
        elif autotrain_model == True:
            self.random_forest = self.stock_analyzer_train_model(None)
        else:
            self.random_forest = None
        self.scraper = StockScraper(advanced_webscrape=True)
    def stok_analyzer_onehot_code_data(self,dataset):
        if isinstance(dataset, pd.DataFrame):
            for column in dataset.columns:
                '''One could probably construct counterexamples where this logic is not sufficient
                but for this particular instance, it is'''
                if dataset[column].dtype != np.number:
                    dataset[column] = self.enc.fit_transform(dataset[column])
                ''' If not a pandas dataframe, blindly assume it must be a list of lists'''
        else:
            for index, value in dataset:
                if isinstance(value, str):
                    pass #dataset[ =  self.enc.fit_transform(dataset[column])
        return dataset
    def stock_analyzer_train_model(self):
        if self.use_portfolio_for_training:
            '''Read in the subset of columns that we will be using for training data, in said order'''
            self.training_data = pd.read_csv(f"{self.userhome}/stockscraper_config/items.csv", usecols=['currency', 'current_price','target_price', 'sector', 'industry','country','analyst_rating','pb_ratio','pe_ratio', 'peg_ratio','ev_ebitda_ratio', 'market_cap_in_ref_currency', 'profit_margin'])[['currency', 'current_price','target_price', 'sector', 'industry','country','analyst_rating','pb_ratio','pe_ratio', 'peg_ratio','ev_ebitda_ratio', 'market_cap_in_ref_currency', 'profit_margin']]
        else:
            pass
        training_data = self.training_data.loc[:, self.training_data.columns != "analyst_rating"]
        analyst_ratings = self.training_data.loc[:, self.training_data.columns == "analyst_rating"]
        training_data = self.enc.fit_transform(training_data)
        clf = RandomForestClassifier(n_estimators=10)
        clf = clf.fit(training_data, analyst_ratings)
        for index_of_tree, iterated_tree in enumerate(self.random_forest):
            fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=800)
            tree.plot_tree(iterated_tree,
                           feature_names = training_data.columns, 
                           class_names=["Strong buy","Buy","Hold","Underperform","Sell"],
                           filled = True)
            fig.savefig(f'{self.user_home}/stockscraper_config/random_forest_treesforest_tree_{index_of_tree}.png')
        with open('path/to/file', 'wb') as model:
            pickle.dump(clf, model)
        return clf
    def stock_analyzer_map_num_rating_to_str_rating(self, rating):
        if rating <=2:
            "Strong buy"
        elif rating <=3:
            "Buy"
        elif rating <=4:
            "Hold"
        elif rating <=5:
            "Underperform"
        else:
            "Sell"  
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

    def stock_analyser_get_rating_analysis_report(self, ticker):
        if self.random_forest == None:
            raise Exception("Model is not yet defined")
        ticker_information = self.scraper.scraper_all_item_info(ticker)
        actual_ticker_rating = ticker_information['analyst_rating']
        ticker_information = ticker_information.pop('analyst_rating', None).values
        predicted_ticker_rating =  self.random_forest.predict(ticker_information)
        