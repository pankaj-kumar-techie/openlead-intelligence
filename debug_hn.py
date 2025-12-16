
import requests
from bs4 import BeautifulSoup

def debug_hn():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = "https://news.ycombinator.com/show"
    print(f"Fetching {url}")
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.content, 'lxml')
    
    items = soup.find_all('tr', class_='athing')
    print(f"Found {len(items)} items")
    
    if items:
        item = items[0]
        # titleline check
        title_line = item.find('span', class_='titleline')
        print(f"Titleline found: {title_line is not None}")
        if title_line:
            print(title_line.prettify())
        else:
            # Check for alternative 'title' class?
            title_cell = item.find('td', class_='title')
            print(f"Title cell found: {title_cell is not None}")
            if title_cell:
                print(title_cell.prettify())

if __name__ == "__main__":
    debug_hn()
