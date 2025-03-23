import json
import os
from Repos.MarketDataRepo import MarketDataRepo as mdrepo
from Services.MarketDataService import MarketDataService as mdservice

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {
        "num_elements": 15,
        "min_value": 1e6,
        "mis_sec_lvl": -1
    }

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

def main():
    service = mdservice()
    repo = mdrepo()
    
    config = load_config()
    
    while True:
        print("\nCurrent Config:")
        for key, value in config.items():
            print(f"{key}: {value}")
        
        print("\nOptions:")
        print("1. Change num_elements")
        print("2. Change min_value")
        print("3. Change mis_sec_lvl")
        print("4. Update price data")
        print("5. Run script")
        print("6. Exit")
        
        choice = input("Select an option: ")
        
        if choice == "1":
            config["num_elements"] = int(input("Enter new num_elements: "))
        elif choice == "2":
            config["min_value"] = float(input("Enter new min_value: "))
        elif choice == "3":
            config["mis_sec_lvl"] = int(input("Enter new mis_sec_lvl: "))
        elif choice == "4":
            repo.get_full_price_data()
            print("Price data updated.")
        elif choice == "5":
            save_config(config)
            run_script(service, repo, config)
        elif choice == "6":
            save_config(config)
            break
        else:
            print("Invalid choice. Please try again.")

def run_script(service, repo, config):
    num_elements = config["num_elements"]
    min_value = config["min_value"]
    mis_sec_lvl = config["mis_sec_lvl"]
    
    sectors = repo.get_systems_above_security_threshold(mis_sec_lvl)
    best_deals = service.find_best_margo(num_elements, min_value, sector_list=sectors)
    
    for item_id, deal in best_deals.items():
        sec_sell = deal["sell"]["sector"]
        sec_buy = deal["buy"]["sector"]
        
        to_print = f"\nitem: {repo.get_item_name(item_id)} ({item_id})"
        to_print += f"\n\tmargo: {deal['margo']}"
        to_print += f"\n\tto buy in: ({repo.get_sector_security_level(repo.fetch_random_system(sec_sell))}) '{repo.get_item_name(sec_sell)}' for: {deal['sell']['price']} volume: {deal['sell']['volume']}"
        to_print += f"\n\tto sell in: ({repo.get_sector_security_level(repo.fetch_random_system(sec_buy))}) '{repo.get_item_name(sec_buy)}' for: {deal['buy']['price']} volume: {deal['buy']['volume']}"
        to_print += f"\n\tjumps between: {repo.get_jump_count(sec_sell, sec_buy)}"
        
        print(to_print)

if __name__ == "__main__":
    main()