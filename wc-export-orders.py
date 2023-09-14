import os
import requests
import time
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# WooCommerce API credentials
store_url = os.getenv("STORE_URL")
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
resume_file = "resume_data.json"


def load_resume_data():
    if os.path.exists(resume_file):
        with open(resume_file, 'r') as file:
            return json.load(file)
    return {'page': 1, 'total_pages': 1}

def save_resume_data(resume_data):
    with open(resume_file, 'w') as file:
        json.dump(resume_data, file)

def save_orders_to_json(orders, page):
    directory = "orders_per_page"
    if not os.path.exists(directory):
        os.mkdir(directory)
    
    filename = f"page_{page}_orders.json"
    filepath = os.path.join(directory, filename)
    
    with open(filepath, mode='w', encoding='utf-8') as file:
        json.dump(orders, file, indent=4)

def pull_orders_from_api(year):
    resumption_data = load_resume_data()
    page = resumption_data['page']
    total_pages = resumption_data['total_pages']
    
    while page <= total_pages:
        try:
            url = f"{store_url}/wp-json/wc/v3/orders?page={page}&per_page=100&after={year}-01-01T00:00:00Z&before={year+1}-01-01T00:00:00Z&order=asc"
            response = requests.get(url, auth=(consumer_key, consumer_secret), timeout=10)
            response.raise_for_status()
            
            orders = response.json()
            save_orders_to_json(orders, page)  # Save orders to a JSON file per page
            
            total_pages = int(response.headers.get('X-WP-TotalPages'))
            page += 1
            
            # Pause for 12 seconds after every 5th request to comply with rate limiting
            if page % 5 == 0:
                time.sleep(60)
        
        except (requests.Timeout, requests.RequestException) as e:
            print(f"Error: {str(e)}. Resuming from page {page} after 60 seconds...")
            time.sleep(60)
            continue
        
        resumption_data['page'] = page
        resumption_data['total_pages'] = total_pages
        save_resume_data(resumption_data)
        
    if page > total_pages and os.path.exists(resume_file):
        os.remove(resume_file)

year = 2019
pull_orders_from_api(year)