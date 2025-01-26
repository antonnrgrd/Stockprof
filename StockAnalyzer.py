'''
from sklearn import model_selection
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from StockScraper import StockScraper
import matplotlib.pyplot as plt
import os
import pickle
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import LabelEncoder

import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_openml
from sklearn.feature_selection import SelectPercentile, chi2
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
'''
from StockScraper import *
columns_to_drop = ["ticker", "holding", "initial_price"]
class StockAnalyzer(StockScraper):
    def __init__(self, autotrain_model=False,use_portfolio_for_training=False):
        super().__init__()
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
        self.scraper = StockScraper()
    def stock_analyzer_train_model(self):
        training_data = None
        training_data_labels = None
        try:
            training_data = pd.read_csv(f"{os.path.expanduser('~')}/stockscraper_config/training_data.csv")
            training_data_labels = pd.read_csv(f"{os.path.expanduser('~')}/stockscraper_config/training_data_labels.csv")
        except:
            print("yo mama")
        random_forest = RandomForestClassifier()
        random_forest.fit(training_data.values, training_data_labels.values)
        with open(f"{os.path.expanduser('~')}/stockscraper_config/best_model.pkl", 'wb') as f:  # open a text file
            pickle.dump(random_forest, f) 
                
       
       
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
        stock_rating = self.scraper_get_stock_rating(ticker)
        model = pickle.load(f"{os.path.expanduser('~')}/stockscraper_config/best_model.pkl")
        ticker_info = self.scraper_all_item_info(ticker)
        ticker_info_as_dict = {}
        for ticker_info in ticker_attributes:
            ticker_info_as_dict[ticker_info] = ticker_info[ticker_info]
        ticker_info = ticker_info_as_dict.values()
        return model.predict(ticker_info)
        
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
        
    def stock_analyser_encode_columns(self, tickers):
        numeric_features =  list(tickers.select_dtypes(include='number'))
        numeric_transformer = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
        )
        categorical_features = list(tickers.select_dtypes(include='string'))
        categorical_transformer = Pipeline(
            steps=[
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ("selector", SelectPercentile(chi2, percentile=50)),
        ]
        )
        assert len(numeric_features) + len(categorical_features) == len(tickers.columns), "Some columns types are likely not considered during encdoing of training data"
        
    def stock_analyser_encode_training_data(self):
        tickers = pd.read_csv(f"{os.path.expanduser('~')}/stockscraper_config/items.csv")
        tickers = tickers.drop(columns_to_drop,axis=1)
        encoded_ticker_data = self.stock_analyser_encode_columns(tickers)