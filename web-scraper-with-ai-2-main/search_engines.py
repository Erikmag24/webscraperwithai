#search_engines.py

import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from config import SEARCH_ENGINES
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_search_results(query: str, search_engine: str, num_pages: int) -> List[str]:
    """
    Scrape search results from a specified search engine with retry and error handling.

    Args:
        query (str): The search query.
        search_engine (str): The name of the search engine to use.
        num_pages (int): Number of result pages to scrape.

    Returns:
        List[str]: A list of unique result URLs.
    """
    # Get the base URL for the specified search engine
    base_url = SEARCH_ENGINES.get(search_engine)
    if not base_url:
        logging.error(f"Unsupported search engine: {search_engine}")
        return []

    # Set up the Chrome WebDriver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        logging.info("Chrome WebDriver started successfully.")
    except WebDriverException as e:
        logging.critical(f"Failed to start Chrome WebDriver: {e}")
        return []

    results = set()  # Use a set to avoid duplicate URLs

    try:
        for page in range(num_pages):
            # Construct the URL for each page of results
            url = f"{base_url}{query}&start={page * 10}"
            retry_attempts = 3  # Set the retry limit
            while retry_attempts > 0:
                try:
                    driver.get(url)
                    logging.info(f"Accessing {url}")

                    # Wait for the page to load
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    logging.info(f"Page {page + 1} loaded successfully.")
                    break
                except TimeoutException:
                    retry_attempts -= 1
                    logging.warning(f"Page {page + 1} took too long to load. Retrying... ({3 - retry_attempts} attempts left)")
                    if retry_attempts == 0:
                        logging.error(f"Page {page + 1} failed to load after multiple attempts. Skipping.")
                        continue

            # Parse the page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = soup.find_all('a')

            # Extract and filter valid result URLs
            for link in links:
                href = link.get('href')
                if href and isinstance(href, str) and href.startswith('http') and not href.startswith(base_url):
                    results.add(href)
                    logging.info(f"Found link: {href}")

    except WebDriverException as e:
        logging.error(f"WebDriver encountered an error: {e}")
    finally:
        driver.quit()
        logging.info("Chrome WebDriver closed.")

    logging.info(f"Total unique links collected: {len(results)}")
    return list(results)
