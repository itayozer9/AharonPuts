import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
from itertools import cycle
import os

def get_options_data(ticker, option_date, percentage, headers):
    url = f"https://finviz.com/quote.ashx?t={ticker}&ta=1&p=d&ty=oc&e={option_date}"
    print(f"Fetching URL: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker} with expiration date {option_date}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    script = soup.find('script', {'id': 'route-init-data'})
    
    if not script:
        raise Exception("Failed to find options data in the page")
    
    data = json.loads(script.string)
    options = data.get('options', [])
    last_close = data.get('lastClose')
    
    if not last_close:
        raise Exception("Failed to find last closing price of the stock")
    
    target_strike = last_close * (1 - percentage / 100)
    
    # Find the nearest strike price
    nearest_option = min(options, key=lambda x: abs(x['strike'] - target_strike) if x['type'] == 'put' else float('inf'))
    
    if nearest_option['type'] != 'put':
        raise Exception("No put option found near the target strike price")
    
    bid_price = nearest_option['bidPrice']
    strike_price = nearest_option['strike']
    
    return {
        'ticker': ticker,
        'last_close': last_close,
        'strike_price': strike_price,
        'bid_price': bid_price
    }

# Function to rotate headers
def get_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15"
    ]
    headers = cycle([{"User-Agent": agent} for agent in user_agents])
    return headers

# Main function
def main(symbols, option_date, percentage):
    results = []
    headers = get_headers()
    
    for ticker in symbols:
        try:
            header = next(headers)
            data = get_options_data(ticker, option_date, percentage, header)
            results.append(data)
            # Random delay between 1 to 5 seconds
            time.sleep(random.uniform(1, 5))
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    
    # Ensure the output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Write results to CSV
    csv_file = f"output/options_data_{option_date}_{percentage}.csv"
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['symbol', 'stock_price', 'strike_price', 'bid_price'])
        for row in results:
            writer.writerow([row['ticker'], row['last_close'], row['strike_price'], row['bid_price']])
    
    print(f"Data written to {csv_file}")

if __name__ == "__main__":
    # Example usage, replace with your actual parameters
    symbols = ["AAPL", "MSFT", "GOOGL"]
    option_date = '2024-07-26'
    percentage = 15
    main(symbols, option_date, percentage)