# print(array[array % 2 == 0])
#  array = np.array([1,2,3,4,5,6,7,8,9,10,14,18,20])
class GEStatus:
    def __init__(self):
        self.collected_info = None
        self.formatted_info = []
        self.notable_events = []
    def add_formatted_info(self, name, price, price_change=None, returns=None, current_holding=None):
        if price_change:      
            self.formatted_info.append("Item: {iname} , current price : {price}, daily price change : {change}, returns {returns}  \n".format(iname = name, price=price, change=price_change, returns=returns))
        else:
            self.formatted_info.append("Item: {iname} , current price : {price}  \n".format(iname = name, price=price))
    def add_formatted_alert(self, name, price, price_change=None, returns = None, earnings=None,current_holding=None):
        if price_change:      
            self.formatted_info.append("Item: {iname}, current price : {price}, daily price change : {change}, returns {returns} \n".format(iname = name, price=price, change=price_change, returns=returns))
        else:
            self.formatted_info.append("Item: {iname}, changing rapidly in price. Its current price : {price}  \n".format(iname = name, price=price))        