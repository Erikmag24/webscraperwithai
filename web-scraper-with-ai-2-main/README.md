# Web Scraping and AI Analysis Project

## Overview

This project is a web scraping application that utilizes various search engines and AI models to extract and analyze information from web pages and/or file based on a search query.

## Key Features

- Support for multiple search engines (Google, Bing, DuckDuckGo, Yahoo, Baidu, Gibiru)
- Automatic query translation into different languages
- Use of AI models (Ollama, Cohere, GPT) for extracted text analysis
- Error handling and connection retry mechanisms
- Result aggregation for final synthesis

## Getting Started

### Prerequisites

- Python 3.x
- Chrome browser
- ChromeDriver compatible with your Chrome version

### Installation

1. Clone the repository or download the project files.

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure paths and API keys:
   - Open `config.py` and insert the correct API keys for the services used (OpenAI, Cohere)


### Usage

1. Run the application:
   ```
   python app.py
   ```

2. Customize the execution in `config.py` or throught the web app at config in http://127.0.0.1:5000/:
   - Modify the search query
   - Adjust the languages for translation
   - Select the search engines to use
   - Choose the AI models to employ (Ollama, Cohere, GPT)


## Important Notes

- Ensure a stable internet connection before running the application.
- Verify that all API services are correctly configured and accessible.
- The project uses web scraping, so be mindful of the terms of service of the websites you're scraping.
- Respect rate limits and use the application responsibly.

## Troubleshooting

- If you encounter connection errors, check your internet connection and firewall settings.
- For API-related issues, verify your API keys and account status with the respective services.
- If the ChromeDriver fails to start, ensure it's compatible with your Chrome browser version.

