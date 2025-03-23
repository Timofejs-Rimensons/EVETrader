from Repos.MarketDataRepo import MarketDataRepo as mdrepo
from tqdm import tqdm
from itertools import islice
import json
import statistics

class MarketDataService():

    def __init__(self):
        self.repo = mdrepo()

    def read_prices(self)-> dict:
        with open("data/market_prices.json", "r") as file:
            market_prices = json.load(file)
        return market_prices
    
    def find_best_margo(self, num_of_elements: int, min_value: int=0, max_value: int=1e12, sector_list: list=[])-> dict:

        market_prices = self.read_prices()

        item_best_prices = {}
        for item, prices in tqdm(iterable=market_prices.items(), desc="Searching items best prices", unit="item"):

            sell_prices = [
                lot["price"]
                for region in prices.values()
                for lot in region['sell']
            ]
            if sell_prices:
                if statistics.median(sell_prices) < 500:
                    continue

            item_best_prices[item] = {"sell": {"price": 1e12, "volume": 0, "sector": -1}, "buy": {"price": 0, "volume": 0, "sector": -1}, "margo": 0}

            sector_mean_prices = {"sell": {}, "buy": {}}
            for sector, price in prices.items(): # Selects the best sell/buy from all sectors
        
                if sector_list and (int(sector) not in sector_list):
                    continue
                
                sell_price_per_one = 1e12
                buy_price_per_one = 0

                if price["sell"]: # Get sell_price_per_one
             
                    if not (price["sell"][0]["price"] > max_value):

                        total_price_sell = 0
                        total_volume_sell = 0
                        for slot in price["sell"]:
                            total_price_sell += slot["price"] * slot["volume"]
                            total_volume_sell += slot["volume"]
                        

                        if not(total_price_sell < min_value):

                            sell_price_per_one = total_price_sell / total_volume_sell

                
                if price["buy"]: # Get buy_price_per_one

                    if not (price["buy"][0]["price"] > max_value):

                        total_price_buy = 0
                        total_volume_buy = 0
                        for slot in price["buy"]:
                            total_price_buy += slot["price"] * slot["volume"]
                            total_volume_buy += slot["volume"]
                        

                        if not(total_price_buy < min_value):

                            buy_price_per_one = total_price_buy / total_volume_buy

                if sell_price_per_one < item_best_prices[item]["sell"]["price"]: # Selects the best sell from all sectors

                    sector_sell = sector
                    if '10000002' in prices:
                        jita_price = prices['10000002']["sell"]
                        if jita_price:
                            if jita_price[0]["price"] < sell_price_per_one*1.15:
                                sell_price_per_one = jita_price[0]["price"]
                                sector_sell = 10000002 # Jita is in the Domain region, region ID is 10000002

                    item_best_prices[item]["sell"]["price"] = sell_price_per_one
                    item_best_prices[item]["sell"]["sector"] = sector_sell
                    item_best_prices[item]["sell"]["volume"] = total_volume_sell

                if buy_price_per_one > item_best_prices[item]["buy"]["price"]: # Selects the best buy from all sectors
                    sector_buy = sector

                    item_best_prices[item]["buy"]["price"] = buy_price_per_one
                    item_best_prices[item]["buy"]["sector"] = sector_buy
                    item_best_prices[item]["buy"]["volume"] = total_volume_buy

                item_best_prices[item]["margo"] = round(item_best_prices[item]["buy"]["price"] / item_best_prices[item]["sell"]["price"], 2)


        item_best_prices = dict(sorted(item_best_prices.items(), key=lambda item: item[1]["margo"], reverse=True))
        return dict(islice(item_best_prices.items(), num_of_elements))
