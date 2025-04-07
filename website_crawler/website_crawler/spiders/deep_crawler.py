import scrapy
from website_crawler.items import WebsiteItem
from urllib.parse import urljoin, urlparse
from datetime import datetime


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

    def parse(self, response):
        # Create item for the current page
        item = WebsiteItem()
        item['url'] = response.url
        item['title'] = response.css('title::text').get()
        item['content'] = response.css('body::text').getall()
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
