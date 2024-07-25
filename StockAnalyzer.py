from sklearn import tree
from sklearn import model_selection
import numpy as np
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
from sklearn import preprocessing
class StockAnalyzer:
    def __init__(self, autotrain_model=False,use_portfolio_for_training=False):
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
        random_forest.fit(training_data, training_data_labels)
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
        
    def stock_analyzer_encode_columns_to_numerical(self,df):
        for column in df.columns:
            if not is_numeric_dtype(df[column]):
                one_hot = pd.get_dummies(df[column])
                df = df.drop(column,axis = 1)
                df = pd.concat([df, one_hot], axis=1)
        return df
    def stock_analyzer_encode_training_data(self):
        stock_data = pd.read_csv(f"{os.path.expanduser('~')}/stockscraper_config/items.csv")
        stock_data = stock_data.drop_duplicates(subset=['ticker'])
        analyst_rating_labels = stock_data[["analyst_rating"]].copy()
        stock_data.drop("analyst_rating", axis=1)
        stock_data_encoded = self.stock_analyzer_encode_columns_to_numerical(stock_data)
        le = preprocessing.LabelEncoder()
        analyst_rating_labels['analyst_rating'] = le.fit_transform(analyst_rating_labels['analyst_rating'] )
        stock_data_encoded.to_csv(f"{os.path.expanduser('~')}/stockscraper_config/training_data.csv")
        analyst_rating_labels.to_csv(f"{os.path.expanduser('~')}/stockscraper_config/training_data_labels.csv")