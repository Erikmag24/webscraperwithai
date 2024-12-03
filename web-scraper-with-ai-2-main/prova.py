import requests
import time
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse
from transformers import pipeline
from gpt_api import generate_with_gpt
import random
import networkx as nx
import matplotlib.pyplot as plt
from config import PROMPT_SCRAPER_SUMMARIZE
import os
import json
import plotly.graph_objects as go
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib

matplotlib.use('Agg')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperConfig:
    def __init__(self, query, search_engine, num_pages, recursion_depth, max_links_per_page=10, timeout=100, max_retries=3, min_delay=1, max_delay=5):
        self.query = query
        self.search_engine = search_engine.lower()
        self.num_pages = num_pages
        self.recursion_depth = recursion_depth
        self.max_links_per_page = max_links_per_page
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_delay = min_delay
        self.max_delay = max_delay

class RecursiveScraper:
    def __init__(self, config):
        self.config = config
        self.visited_urls = set()
        self.text_data = {}
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.graph = nx.DiGraph()

    def fetch(self, url):
        retries = 0
        while retries < self.config.max_retries:
            try:
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': 'https://www.google.com/'
                }
                response = requests.get(url, headers=headers, timeout=self.config.timeout)
                if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                    time.sleep(random.uniform(self.config.min_delay, self.config.max_delay))
                    return response.text
                else:
                    logger.debug(f"Non-HTML content or invalid status code for {url}")
                    return None
            except Exception as e:
                retries += 1
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                logger.warning(f"Error fetching {url}: {e}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
        logger.error(f"Failed to fetch {url} after {self.config.max_retries} retries.")
        return None

    def scrape_page(self, url, current_depth, parent_url=None):
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)
        logger.info(f"Scraping {url} at depth {current_depth}")

        if parent_url:
            self.graph.add_edge(parent_url, url)
        else:
            self.graph.add_node(url)

        try:
            html = self.fetch(url)
            if html is None:
                return
            soup = BeautifulSoup(html, 'html.parser')

            text = self.extract_text(soup)
            if text:
                self.text_data[url] = text

            if current_depth < self.config.recursion_depth:
                links = self.extract_links(soup, url)
                random.shuffle(links)
                for link in links[:self.config.max_links_per_page]:
                    self.scrape_page(link, current_depth + 1, parent_url=url)
        except Exception as e:
            logger.error(f"Error scraping {url} at depth {current_depth}: {e}")

    def extract_text(self, soup):
        for script_or_style in soup(['script', 'style', 'noscript']):
            script_or_style.decompose()
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_links(self, soup, base_url):
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            href = urljoin(base_url, href)
            parsed_href = urlparse(href)
            if parsed_href.scheme in ('http', 'https'):
                if href not in self.visited_urls:
                    links.append(href)
        return links

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

    def summarize_text(self):
        if not self.text_data:
            return "No text to summarize."

        summaries = {}
        logger.info("Starting text summarization for each URL.")

        from transformers import BartTokenizer
        tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

        for url, text in self.text_data.items():
            logger.info(f"Summarizing {url}")
            try:
                inputs = tokenizer(text, max_length=1024, truncation=True, return_tensors='pt')
                summary_ids = self.summarizer.model.generate(inputs['input_ids'], max_length=130, min_length=30, do_sample=False)
                summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                llm_summary = generate_with_gpt(text + " " + PROMPT_SCRAPER_SUMMARIZE)
                summaries[url] = (summary or "") + " Modello LLM: " + (llm_summary or "")
                logger.info(f"Summarization completed for {url}.")
            except Exception as e:
                logger.error(f"Error summarizing {url}: {e}")
                summaries[url] = "Summary unavailable due to an error."

        return summaries

    def generate_link_graph_static(self):
        logger.info("Generating static link graph.")
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        nx.draw(self.graph, pos, with_labels=False, node_size=50, alpha=0.7, arrows=True)
        for key, value in pos.items():
            plt.text(value[0], value[1], s=key, fontsize=5)
        plt.title("Link Hierarchy Graph")
        graph_path = os.path.join('static', 'link_graph_static.png')
        plt.savefig(graph_path)
        plt.close()
        logger.info(f"Static link graph saved as {graph_path}.")

    def generate_link_graph_interactive(self):
        logger.info("Generating interactive link graph.")
        pos = nx.spring_layout(self.graph)
        edge_x, edge_y = [], []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1), hoverinfo='none', mode='lines')
        node_x, node_y, node_text = [], [], []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers+text', text=node_text,
            hoverinfo='text', marker=dict(size=10))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(title="Interactive Link Graph", showlegend=False, hovermode='closest'))
        
        interactive_path = os.path.join('static', 'link_graph_interactive.html')
        fig.write_html(interactive_path)
        logger.info(f"Interactive link graph saved as {interactive_path}.")

    def generate_link_graph_interactive_zoomable(self):
        logger.info("Generating custom interactive hierarchical link graph with Plotly (Bottom to Top).")
        
        levels = {}
        max_level = 0

        for node in nx.topological_sort(self.graph):
            preds = list(self.graph.predecessors(node))
            level = levels[preds[0]] + 1 if preds else 0
            levels[node] = level
            max_level = max(max_level, level)

        node_positions = {}
        nodes_in_level = {}
        horizontal_spacing = 1
        vertical_spacing = 2

        for node, level in levels.items():
            if level not in nodes_in_level:
                nodes_in_level[level] = []
            nodes_in_level[level].append(node)

        for level, nodes in nodes_in_level.items():
            y_position = -level * vertical_spacing
            x_start = -((len(nodes) - 1) * horizontal_spacing) / 2

            for i, node in enumerate(nodes):
                x_position = x_start + i * horizontal_spacing
                node_positions[node] = (x_position, y_position)

        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = node_positions[edge[0]]
            x1, y1 = node_positions[edge[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        node_x = []
        node_y = []
        node_text = []
        node_depths = []

        for node, (x, y) in node_positions.items():
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_depths.append(levels[node])

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="bottom center",
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                color=node_depths,
                size=10,
                colorbar=dict(
                    title="Node Depth",
                    titleside="right"
                ),
                line_width=0.5
            )
        )

        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title="Interactive Hierarchical Link Graph (Bottom to Top)",
                            title_x=0.5,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20, l=5, r=5, t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            width=1200,
                            height=800
                        ))

        interactive_path = os.path.join('static', 'link_graph_interactive_zoomable.html')
        fig.write_html(interactive_path)
        logger.info(f"Interactive hierarchical link graph saved as {interactive_path}.")

    def generate_link_graph_json(self):
        logger.info("Exporting link graph to JSON format.")
        data = nx.node_link_data(self.graph)
        json_path = os.path.join('static', 'link_graph.json')
        with open(json_path, 'w') as json_file:
            json.dump(data, json_file)
        logger.info(f"Link graph JSON saved as {json_path}.")

    def generate_all_graphs(self):
        self.generate_link_graph_static()
        self.generate_link_graph_interactive()
        self.generate_link_graph_json()
        self.generate_link_graph_interactive_zoomable()

def get_search_results(query, search_engine, num_results):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By

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