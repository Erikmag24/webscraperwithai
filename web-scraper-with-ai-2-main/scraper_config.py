#scraper_config.py

import random

class ScraperConfig:
    def __init__(
        self, query, search_engine, num_pages, recursion_depth,
        max_links_per_page=10, timeout=100, max_retries=3,
        min_delay=1, max_delay=5
    ):
        self.query = query
        self.search_engine = search_engine.lower()
        self.num_pages = num_pages
        self.recursion_depth = recursion_depth
        self.max_links_per_page = max_links_per_page
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_delay = min_delay
        self.max_delay = max_delay

    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (X11; Linux x86_64)',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
            'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)',
            'Mozilla/5.0 (Android 11; Mobile; rv:88.0)',
        ]
        return random.choice(user_agents)
