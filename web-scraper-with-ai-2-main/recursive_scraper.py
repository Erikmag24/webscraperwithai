#recursive_scraper.py

import requests
import time
import random
import re
import os
import json
import logging
import networkx as nx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from transformers import pipeline, BartTokenizer
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from config import PROMPT_SCRAPER_SUMMARIZE
from gpt_api import generate_with_gpt

logger = logging.getLogger(__name__)

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
                    'User-Agent': self.config.get_random_user_agent(),
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
            if parsed_href.scheme in ('http', 'https') and href not in self.visited_urls:
                links.append(href)
        return links

    def summarize_text(self):
        if not self.text_data:
            return "No text to summarize."

        summaries = {}
        logger.info("Starting text summarization for each URL.")

        tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

        for url, text in self.text_data.items():
            logger.info(f"Summarizing {url}")
            try:
                inputs = tokenizer(text, max_length=1024, truncation=True, return_tensors='pt')
                summary_ids = self.summarizer.model.generate(
                    inputs['input_ids'],
                    max_length=130,
                    min_length=30,
                    do_sample=False
                )
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
            hoverinfo='text', marker=dict(size=10)
        )

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
