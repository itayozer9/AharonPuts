import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
from itertools import cycle
import os
from datetime import datetime

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
    
    bid_price = nearest_option['bidPrice'] * 100  # Premium (bid price multiplied by 100)
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

# Calculate the number of days to expiration
def calculate_days_to_expiration(option_date):
    expiration_date = datetime.strptime(option_date, "%Y-%m-%d")
    today = datetime.today()
    return (expiration_date - today).days

# Main function
def main(symbols, option_date, percentage):
    results = []
    headers = get_headers()
    days_to_expiration = calculate_days_to_expiration(option_date)
    
    for ticker in symbols:
        try:
            header = next(headers)
            data = get_options_data(ticker, option_date, percentage, header)
            collateral = data['last_close'] * 20
            yield_percentage = (1 / collateral) * (data['bid_price'] / days_to_expiration * 365) * 100
            data['collateral'] = collateral
            data['yield'] = yield_percentage
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
        writer.writerow(['symbol', 'stock_price', 'strike_price', 'bid_price', 'collateral', 'yield'])
        for row in results:
            writer.writerow([
                row['ticker'], 
                f"{row['last_close']:.2f}" if not float(row['last_close']).is_integer() else int(row['last_close']), 
                f"{row['strike_price']:.2f}" if not float(row['strike_price']).is_integer() else int(row['strike_price']), 
                f"{row['bid_price']:.2f}" if not float(row['bid_price']).is_integer() else int(row['bid_price']),
                f"{row['collateral']:.2f}" if not float(row['collateral']).is_integer() else int(row['collateral']),
                f"{row['yield']:.2f}" if not float(row['yield']).is_integer() else int(row['yield'])
            ])
    
    print(f"Data written to {csv_file}")