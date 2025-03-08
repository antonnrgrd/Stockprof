

from StockScraper import StockScraper
import os
import pickle
import pandas as pd
from  sklearn.preprocessing import LabelBinarizer
from keras.layers import LeakyReLU



from StockScraper import *
import tensorflow as tf
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

                
            
    def stock_analyzer_predict(self,ticker):
        stock_rating = self.scraper_get_stock_rating(ticker)
        model = pickle.load(f"{os.path.expanduser('~')}/stockscraper_config/best_model.pkl")
        ticker_info = self.scraper_all_item_info(ticker)
        ticker_info_as_dict = {}
        for ticker_info in ticker_attributes:
            ticker_info_as_dict[ticker_info] = ticker_info[ticker_info]
        ticker_info = ticker_info_as_dict.values()
        return model.predict(ticker_info)
        
  

    def stock_analyzer_get_rating_analysis_report(self, ticker):
        if self.random_forest == None:
            raise Exception("Model is not yet defined")
        ticker_information = self.scraper.scraper_all_item_info(ticker)
        actual_ticker_rating = ticker_information['analyst_rating']
        ticker_information = ticker_information.pop('analyst_rating', None).values
        predicted_ticker_rating =  self.random_forest.predict(ticker_information)
      
    @classmethod
    def stock_analyzer_map_categorical_to_numerical(self, tickers : pd.DataFrame) -> dict:

        binarizer = LabelBinarizer()
        training_data_labels = binarizer.fit_transform(tickers["analyst_rating"].values)
        tickers.drop(["analyst_rating"], inplace=True, axis=1)
        training_data = pd.get_dummies(tickers, dtype=int).values
                                                   
        #catergorical_columns = list(tickers.select_dtypes(include=['object']))
       # for column in catergorical_columns:
        #    label_binarizer.fit(tickers[column].values)
        #    tickers[f"{column}_encoded"] = list(label_binarizer.transform(tickers[column].values))
        #    tickers.drop([column], inplace=True, axis=1)
       # training_data  = tickers.loc[:, tickers.columns != 'analyst_rating_encoded'].values
       # training_data_labels = tickers["analyst_rating_encoded"].values
        return {'training_data': training_data, 'training_data_labels':training_data_labels}
    
    def stock_analyser_define_model(self,num_classes, input_size):
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(input_size, activation=LeakyReLU()))
        model.add(tf.keras.layers.Dense(512, activation=LeakyReLU()))
        model.add(tf.keras.layers.Dense(512, activation=LeakyReLU()))
        model.add(tf.keras.layers.Dense(512, activation=LeakyReLU()))
        model.add(tf.keras.layers.Dense(512, activation=LeakyReLU()))
        model.add(tf.keras.layers.Dense(num_classes, activation='softmax'))
        model.compile(optimizer="adam",loss="categorical_crossentropy", metrics=["accuracy"])
        
        return model
    def stock_analyzer_train_model(self):
        tickers = pd.read_csv(f"{os.path.expanduser('~')}/stockscraper_config/items.csv")
        
        tickers = tickers.drop(columns_to_drop, axis=1)
        
        training_data = self.stock_analyzer_map_categorical_to_numerical(tickers)
        model = self.stock_analyser_define_model(training_data['training_data_labels'].shape[1],training_data['training_data'].shape[1])
        model.fit(training_data['training_data'], training_data['training_data_labels'],epochs = 300, validation_split=0.2)
        
    def stock_analyzer_encode_training_data(self):
        tickers = pd.read_csv(f"{os.path.expanduser('~')}/stockscraper_config/items.csv")
        tickers = tickers.drop(columns_to_drop,axis=1)
        encoded_ticker_data = self.stock_analyzer_encode_columns(tickers)