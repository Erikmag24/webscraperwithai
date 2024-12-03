#get_google_search_links.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import urllib.parse
from typing import List
from webdriver_manager.chrome import ChromeDriverManager  # Import WebDriver Manager

def get_google_search_links(query: str, num_pages: int) -> List[str]:
    """
    Scrape Google search results for a given query.

    Args:
        query (str): The search query.
        num_pages (int): Number of result pages to scrape.

    Returns:
        List[str]: A list of unique result URLs, excluding ads and the first result.
    """
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set up the Chrome WebDriver using WebDriver Manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    all_links = set()  # Use a set to avoid duplicate URLs

    try:
        for page in range(num_pages):
            # Construct the Google search URL
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={page * 10}"
            print(f"Navigating to: {url}")
            driver.get(url)

            # Wait for the search results to load
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "search")))
            time.sleep(2)  # Additional wait to ensure dynamic content is loaded

            # Parse the page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find all search result links
            results = soup.find_all('div', class_='yuRUbf')
            for result in results:
                link = result.find('a', href=True)
                if link:
                    href = link['href']
                    # Exclude ads and verify the link
                    if not any(ad in href for ad in ['googleads', 'googleadservices']):
                        all_links.add(href)

            print(f"Found {len(all_links)} unique links so far.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Ensure the driver is closed
        driver.quit()

    # Convert set to list and exclude the first link (often the search page itself)
    return list(all_links)[1:]
