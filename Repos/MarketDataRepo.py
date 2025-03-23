import requests
import json
import time
from tqdm import tqdm
import random
import os
import csv

class MarketDataRepo():
    # ESI Base URL
    def __init__(self):
        self.ESI_URL = "https://esi.evetech.net/latest"
        self.CACHE_FILE = "data/constellation_security.csv"
        self.constellation_security = self.load_cached_data()
        
    def get_item_name(self, item_id):
        url = f"{self.ESI_URL}/universe/names/"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=[item_id], headers=headers)
    
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0].get("name", "Not Found")
            return "Not Found"
        
    def get_jump_count(self, origin_region_id, destination_region_id):
        """Returns the number of jumps between two regions."""
        # Fetch a random system from the origin and destination regions
        origin_system = self.fetch_random_system(origin_region_id)
        destination_system = self.fetch_random_system(destination_region_id)

        # Check if the systems are valid
        if origin_system == -1 or destination_system == -1:

            return -1

        # Fetch the route between the two systems
        url = f"{self.ESI_URL}/route/{origin_system}/{destination_system}/"
        response = requests.get(url)

        if response.status_code == 200:
            route = response.json()

            # If route is empty, return None or handle error
            if not route:
                return -420

            return len(route) - 1  # Exclude the starting system
        else:
            return -404  # Return None if the request fails
        
    def get_sector_security_level(self, system_id):
        url = f"{self.ESI_URL}/universe/systems/{system_id}/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return round(data.get("security_status", -1), 2)
        return -1
    
    def load_cached_data(self):
        """Loads cached constellation security levels from CSV if available."""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, mode="r") as file:
                    reader = csv.reader(file)
                    return {int(row[0]): float(row[1]) for row in reader if row}
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}  # Return empty dict if cache is missing or corrupt

    def save_cached_data(self):
        """Saves constellation security levels to a CSV file."""
        try:
            with open(self.CACHE_FILE, mode="w", newline="") as file:
                writer = csv.writer(file)
                for constellation_id, security in self.constellation_security.items():
                    writer.writerow([constellation_id, security])
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_systems_above_security_threshold(self, threshold=0.5):
        """Returns a list of region IDs where at least one system meets the security threshold."""
        regions_url = f"{self.ESI_URL}/universe/regions/"
        response = requests.get(regions_url)

        if response.status_code != 200:
            print("Error fetching regions list")
            return []

        region_ids = response.json()
        valid_regions = []

        for region_id in tqdm(region_ids, desc=f"Checking security ≥ {threshold}", unit="region"):
            security_status = self.constellation_security.get(region_id)

            if security_status is None:  # If not cached, fetch new data
                rnd_system = self.fetch_random_system(region_id)
                security_status = self.get_sector_security_level(rnd_system)
                self.constellation_security[region_id] = security_status  # Cache it

            if security_status >= threshold:
                valid_regions.append(region_id)

        self.save_cached_data()  # Save all fetched data
        return valid_regions

    def fetch_random_system(self, region_id):
        """Fetches a random system from a region."""
        region_url = f"{self.ESI_URL}/universe/regions/{region_id}/"
        response = requests.get(region_url)

        if response.status_code == 200:
            constellation_ids = response.json().get("constellations", [])
            if not constellation_ids:
                return -1  # No constellations found in the region

            # Pick a random constellation
            random_constellation = random.choice(constellation_ids)

            # Fetch systems from that constellation
            constellation_url = f"{self.ESI_URL}/universe/constellations/{random_constellation}/"
            response = requests.get(constellation_url)

            if response.status_code == 200:
                system_ids = response.json().get("systems", [])
                if not system_ids:
                    return -1  # No systems found in the constellation

                return random.choice(system_ids)  # Return a random system from the constellation

        return -1  # Return -1 if the request fails or no systems are found

    def get_regions(self):
        """Fetch all region IDs."""
        url = f"{self.ESI_URL}/universe/regions/"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else []

    def get_market_orders(self, region_id):
        """Fetch market orders for a specific region."""
        url = f"{self.ESI_URL}/markets/{region_id}/orders/?order_type=all&datasource=tranquility"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else []

    def process_market_data(self, region_id):
        """Get the 3 cheapest sell and 3 highest buy orders for each item."""
        orders = self.get_market_orders(region_id)
        item_prices = {}

        for order in orders:
            type_id = order['type_id']
            price = order['price']
            volume = order['volume_remain']
            is_buy_order = order['is_buy_order']

            if type_id not in item_prices:
                item_prices[type_id] = {'sell': [], 'buy': []}

            order_data = {'price': price, 'volume': volume}

            if is_buy_order:
                item_prices[type_id]['buy'].append(order_data)
            else:
                item_prices[type_id]['sell'].append(order_data)

        # Sort sell orders by price (ascending) and take top 3
        # Sort buy orders by price (descending) and take top 3
        for type_id in item_prices.keys():
            item_prices[type_id]['sell'] = sorted(item_prices[type_id]['sell'], key=lambda x: x['price'])[:3]
            item_prices[type_id]['buy'] = sorted(item_prices[type_id]['buy'], key=lambda x: x['price'], reverse=True)[:3]

        return item_prices

    def get_full_price_data(self):
        """Main function to fetch and save market data."""
        regions = self.get_regions()
        all_prices = {}

        for region_id in tqdm(iterable=regions, desc="Fetching data for regions", unit="reg"):
            # Fetching data
            market_items = self.process_market_data(region_id)

            for type_id, prices in market_items.items():

                if type_id not in all_prices:
                    all_prices[type_id] = {region_id: prices}
                    continue

                all_prices[type_id][region_id] = prices

            time.sleep(0.25)  # Prevent API rate limits

        all_prices_ordered = {}
        for key in sorted(all_prices.keys()):
            all_prices_ordered[key] = all_prices[key]

        # Save data to JSON file
        with open("data/market_prices.json", "w") as f:
            json.dump(all_prices_ordered, f, indent=4)

        print("Market prices saved to market_prices.json")