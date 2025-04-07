import scrapy
from website_crawler.items import WebsiteItem
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
import lxml.html
from lxml_html_clean import Cleaner
from scrapy.exceptions import IgnoreRequest


class DeepCrawlerSpider(scrapy.Spider):
    name = "deep_crawler"
    allowed_domains = []  
    start_urls = [] 
    custom_settings = {
        'DEPTH_LIMIT': 3,  
        'CONCURRENT_REQUESTS': 16,  
        'DOWNLOAD_DELAY': 1,  
        'ROBOTSTXT_OBEY': True,
        # Use streaming for large responses
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
        },
    }
    
    # Track domains to avoid duplicate crawling
    visited_urls = set()

    def __init__(self, urls=None, *args, **kwargs):
        super(DeepCrawlerSpider, self).__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls.split(',')
            # Extract domains from URLs
            self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]
        
        # Initialize HTML cleaner using the new package
        self.cleaner = Cleaner(
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
            # Check content size before processing
            if len(html_content) > 5 * 1024 * 1024:  # 5MB
                self.logger.warning(f"Large HTML content detected ({len(html_content)} bytes), minimal cleaning")
                # For large contents, do simple regex-based cleaning instead of full parsing
                html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content)
                html_content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html_content)
                return html_content
                
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

    def should_follow_url(self, url):
        """Determine if a URL should be followed based on extension"""
        # Skip large binary files, images, videos, etc.
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', 
                          '.mp3', '.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png', 
                          '.gif', '.svg', '.webp', '.iso', '.dmg', '.exe', '.bin']
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in skip_extensions:
            if path.endswith(ext):
                return False
                
        return True
        
    def start_requests(self):
        """Override to add streaming download for large responses"""
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse, meta={'download_maxsize': 10485760})  # 10MB limit

    def parse(self, response):
        # Skip if response is too large or an invalid type
        if not hasattr(response, 'text') or not response.text:
            self.logger.warning(f"Skipping {response.url}: No text content available")
            return
            
        # Avoid processing the same URL twice
        if response.url in self.visited_urls:
            self.logger.debug(f"Already processed {response.url}")
            return
            
        self.visited_urls.add(response.url)
            
        # Create item for the current page
        item = WebsiteItem()
        item['url'] = response.url
        item['title'] = response.css('title::text').get()
        
        try:
            # Extract and clean the full HTML content
            html_content = response.text
            clean_html = self.clean_html(html_content)
            item['content'] = clean_html
        except Exception as e:
            self.logger.error(f"Error processing HTML content for {response.url}: {e}")
            item['content'] = f"<html><body><p>Error processing content: {str(e)}</p></body></html>"
        
        # For text extraction (additional feature)
        text_content = []
        
        try:
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
            text_content = [self.clean_text(text) for text in text_content if text and text.strip()]
            text_content = list(filter(None, text_content))  # Remove empty strings
        except Exception as e:
            self.logger.error(f"Error extracting text from {response.url}: {e}")
            
        # Add extracted text content as a separate field
        item['text_content'] = text_content
        item['timestamp'] = datetime.now().isoformat()

        # Extract all links
        internal_links = []
        external_links = []
        
        try:
            all_links = response.css('a::attr(href)').getall()
            
            for link in all_links:
                try:
                    absolute_url = urljoin(response.url, link)
                    parsed_url = urlparse(absolute_url)
                    
                    # Skip non-HTTP(S) links
                    if not parsed_url.scheme.startswith('http'):
                        continue
                        
                    # Skip if URL shouldn't be followed (based on extension)
                    if not self.should_follow_url(absolute_url):
                        continue

                    # Check if the link is internal or external
                    if any(domain in parsed_url.netloc for domain in self.allowed_domains):
                        internal_links.append(absolute_url)
                        # Follow internal links that we haven't seen yet
                        if absolute_url not in self.visited_urls:
                            yield scrapy.Request(
                                absolute_url, 
                                callback=self.parse,
                                meta={'download_maxsize': 10485760},  # 10MB limit
                                errback=self.handle_error
                            )
                    else:
                        external_links.append(absolute_url)
                except Exception as e:
                    self.logger.error(f"Error processing link {link} from {response.url}: {e}")
        except Exception as e:
            self.logger.error(f"Error extracting links from {response.url}: {e}")

        item['internal_links'] = internal_links
        item['external_links'] = external_links

        yield item
        
    def handle_error(self, failure):
        """Handle request errors"""
        # Extract the request that caused the error
        request = failure.request
        
        self.logger.error(f"Request failed: {request.url} - {repr(failure)}")
        
        # You can add logic here to retry or log specific errors
        if failure.check(IgnoreRequest):
            self.logger.warning(f"IgnoreRequest: {request.url} - This may be due to size limits")
