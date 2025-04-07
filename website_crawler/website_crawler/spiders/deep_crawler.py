import scrapy
from website_crawler.items import WebsiteItem
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
import lxml.html
import lxml.html.clean


class DeepCrawlerSpider(scrapy.Spider):
    name = "deep_crawler"
    allowed_domains = []  
    start_urls = [] 
    custom_settings = {
        'DEPTH_LIMIT': 3,  
        'CONCURRENT_REQUESTS': 16,  
        'DOWNLOAD_DELAY': 1,  
        'ROBOTSTXT_OBEY': True,  
    }

    def __init__(self, urls=None, *args, **kwargs):
        super(DeepCrawlerSpider, self).__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls.split(',')
            # Extract domains from URLs
            self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]
        
        # Initialize HTML cleaner
        self.cleaner = lxml.html.clean.Cleaner(
            style=True,                # Remove CSS styles
            scripts=True,              # Remove JavaScript
            javascript=True,           # Remove JavaScript
            comments=True,             # Remove comments
            embedded=True,             # Remove embedded content like Flash
            frames=True,               # Remove frames
            forms=True,                # Keep forms for structure
            annoying_tags=True,        # Remove tags like <blink> and <marquee>
            meta=False,                # Keep meta tags
            links=False,               # Keep link tags
            page_structure=False,      # Keep head and body tags
            processing_instructions=True,  # Remove processing instructions
            remove_tags=None,          # Don't remove any tags by name
            kill_tags=None,            # Don't kill any tags and their content
        )

    def clean_text(self, text):
        # Remove extra whitespace and normalize spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def clean_html(self, html_content):
        try:
            # Parse the HTML content
            doc = lxml.html.fromstring(html_content)
            # Clean the HTML
            clean_doc = self.cleaner.clean_html(doc)
            # Convert back to string
            clean_html = lxml.html.tostring(clean_doc, pretty_print=True, encoding='unicode')
            return clean_html
        except Exception as e:
            self.logger.error(f"Error cleaning HTML: {e}")
            return html_content  # Return original if cleaning fails

    def parse(self, response):
        # Create item for the current page
        item = WebsiteItem()
        item['url'] = response.url
        item['title'] = response.css('title::text').get()
        
        # Extract and clean the full HTML content
        html_content = response.text
        clean_html = self.clean_html(html_content)
        item['content'] = clean_html
        
        # For text extraction (additional feature)
        text_content = []
        
        # Get text from paragraphs
        paragraphs = response.css('p::text').getall()
        text_content.extend(paragraphs)
        
        # Get text from headings
        headings = response.css('h1::text, h2::text, h3::text, h4::text, h5::text, h6::text').getall()
        text_content.extend(headings)
        
        # Get text from list items
        list_items = response.css('li::text').getall()
        text_content.extend(list_items)
        
        # Get text from divs that might contain content
        div_text = response.css('div:not([class*="header"]):not([class*="footer"]):not([class*="nav"]):not([class*="menu"])::text').getall()
        text_content.extend(div_text)
        
        # Clean and filter the text content
        text_content = [self.clean_text(text) for text in text_content if text.strip()]
        text_content = list(filter(None, text_content))  # Remove empty strings
        
        # Add extracted text content as a separate field
        item['text_content'] = text_content
        item['timestamp'] = datetime.now().isoformat()

        # Extract all links
        all_links = response.css('a::attr(href)').getall()
        internal_links = []
        external_links = []

        for link in all_links:
            absolute_url = urljoin(response.url, link)
            parsed_url = urlparse(absolute_url)
            
            # Skip non-HTTP(S) links
            if not parsed_url.scheme.startswith('http'):
                continue

            # Check if the link is internal or external
            if any(domain in parsed_url.netloc for domain in self.allowed_domains):
                internal_links.append(absolute_url)
                # Follow internal links
                yield scrapy.Request(absolute_url, callback=self.parse)
            else:
                external_links.append(absolute_url)

        item['internal_links'] = internal_links
        item['external_links'] = external_links

        yield item
