
import requests
from bs4 import BeautifulSoup

def debug_clutch():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = "https://clutch.co/web-developers"
    print(f"Fetching {url}")
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.content, 'lxml')
    
    # Check for rows
    rows = soup.find_all('li', class_='provider-row')
    print(f"Found {len(rows)} provider rows")
    
    if not rows:
        # Debug alternative selectors
        print("Checking alternative selectors...")
        articles = soup.find_all('article')
        print(f"Found {len(articles)} articles")
        
        divs = soup.find_all('div', class_=lambda x: x and 'provider-card' in x)
        print(f"Found {len(divs)} provider-card divs")

if __name__ == "__main__":
    debug_clutch()
