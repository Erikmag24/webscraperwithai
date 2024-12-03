#execute_scraping.py

import logging
from scraper_config import ScraperConfig
from recursive_scraper import RecursiveScraper
from search_results import get_search_results

logger = logging.getLogger(__name__)

def execute_scraping(query, search_engine, num_pages, recursion_depth):
    config = ScraperConfig(query, search_engine, num_pages, recursion_depth)
    initial_links = get_search_results(config.query, config.search_engine, config.num_pages)

    if not initial_links:
        logger.error("No initial links found. Exiting.")
        return {}

    scraper = RecursiveScraper(config)
    for link in initial_links:
        scraper.scrape_page(link, current_depth=1)

    scraper.generate_all_graphs()

    summaries = scraper.summarize_text()
    return summaries
