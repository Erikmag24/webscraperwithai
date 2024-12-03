#search_results.py

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

def get_search_results(query, search_engine, num_results):
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    search_urls = {
        'google': 'https://www.google.com/search?q={query}&num={num}',
        'bing': 'https://www.bing.com/search?q={query}&count={num}',
        'baidu': 'https://www.baidu.com/s?wd={query}',
        'duckduckgo': 'https://duckduckgo.com/?q={query}',
        'yahoo': 'https://search.yahoo.com/search?p={query}&n={num}',
        'yandex': 'https://yandex.com/search/?text={query}',
        'ask': 'https://www.ask.com/web?q={query}'
    }

    if search_engine not in search_urls:
        logger.error(f"Search engine {search_engine} not supported.")
        driver.quit()
        return []

    url = search_urls[search_engine].format(query=query, num=num_results)
    driver.get(url)

    links = []
    try:
        if search_engine == 'google':
            results = driver.find_elements(By.CSS_SELECTOR, 'div.g')
            for result in results[:num_results]:
                link_element = result.find_element(By.TAG_NAME, 'a')
                if link_element:
                    link = link_element.get_attribute('href')
                    if link:
                        links.append(link)
        elif search_engine == 'bing':
            results = driver.find_elements(By.CSS_SELECTOR, 'li.b_algo')
            for result in results[:num_results]:
                link_element = result.find_element(By.TAG_NAME, 'a')
                if link_element:
                    link = link_element.get_attribute('href')
                    if link:
                        links.append(link)
        elif search_engine == 'baidu':
            results = driver.find_elements(By.CSS_SELECTOR, 'h3.t > a')
            for result in results[:num_results]:
                link = result.get_attribute('href')
                if link:
                    links.append(link)
        elif search_engine == 'duckduckgo':
            results = driver.find_elements(By.CSS_SELECTOR, 'a.result__a')
            for result in results[:num_results]:
                link = result.get_attribute('href')
                if link:
                    links.append(link)
        elif search_engine == 'yahoo':
            results = driver.find_elements(By.CSS_SELECTOR, 'div.dd.algo')
            for result in results[:num_results]:
                link_element = result.find_element(By.TAG_NAME, 'a')
                if link_element:
                    link = link_element.get_attribute('href')
                    if link:
                        links.append(link)
        elif search_engine == 'yandex':
            results = driver.find_elements(By.CSS_SELECTOR, 'a.Link.Link_theme_normal.organic__url.link_cropped_no.i-bem')
            for result in results[:num_results]:
                link = result.get_attribute('href')
                if link:
                    links.append(link)
        elif search_engine == 'ask':
            results = driver.find_elements(By.CSS_SELECTOR, 'div.PartialSearchResults-item')
            for result in results[:num_results]:
                link_element = result.find_element(By.CSS_SELECTOR, 'a.PartialSearchResults-item-title-link.result-link')
                if link_element:
                    link = link_element.get_attribute('href')
                    if link:
                        links.append(link)
        else:
            logger.error(f"Search engine {search_engine} not supported.")
    except Exception as e:
        logger.error(f"Error extracting search results: {e}")

    driver.quit()
    return links
