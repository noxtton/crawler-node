# Website Crawler

A Scrapy-based web crawler that crawls websites deeply, saves clean HTML content, extracts links, and provides structured data in JSON format.

## Features

- Scrapes and saves clean HTML content (removing scripts, styles, etc.)
- Extracts and stores text content separately
- Follows internal links automatically for deep crawling
- Collects external links
- Organizes output in separate HTML and JSON files

## Installation

1. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   Note: This project uses the `lxml_html_clean` package for HTML cleaning, which is a separate package from `lxml`.

## Usage

### Basic Usage

To crawl a single website:

```bash
cd website_crawler
scrapy crawl deep_crawler -a urls="https://example.com"
```

To crawl multiple websites:

```bash
cd website_crawler
scrapy crawl deep_crawler -a urls="https://example.com,https://another-example.com"
```

### Output

The crawler stores its output in the `output` directory:

- `output/html/`: Contains the clean HTML files (with scripts and styles removed)
- `output/json/`: Contains JSON files with metadata, extracted text, and links

### Configuration

You can modify crawler settings in `website_crawler/spiders/deep_crawler.py`:

- `DEPTH_LIMIT`: How deep the crawler will go (default: 3)
- `CONCURRENT_REQUESTS`: Number of concurrent requests (default: 16)
- `DOWNLOAD_DELAY`: Delay between requests in seconds (default: 1)
- `ROBOTSTXT_OBEY`: Whether to respect robots.txt (default: True)

## License

MIT
