import json
import os
from datetime import datetime
from urllib.parse import urlparse
import codecs
import logging
from scrapy.exceptions import DropItem


class WebsiteCrawlerPipeline:
    def __init__(self):
        # Create output directory if it doesn't exist
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Create subdirectories for HTML and JSON files
        self.html_dir = os.path.join(self.output_dir, 'html')
        self.json_dir = os.path.join(self.output_dir, 'json')
        
        if not os.path.exists(self.html_dir):
            os.makedirs(self.html_dir)
        if not os.path.exists(self.json_dir):
            os.makedirs(self.json_dir)
            
        # Set up logger
        self.logger = logging.getLogger(__name__)
        
        # Maximum content size to process (10MB)
        self.max_content_size = 10 * 1024 * 1024

    def get_filename_from_url(self, url):
        """Generate a filename from a URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('.', '_')
        path = parsed_url.path.replace('/', '_')
        if not path or path == '_':
            path = '_index'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{domain}{path}_{timestamp}"

    def process_item(self, item, spider):
        try:
            # Check content size to prevent memory issues
            content_size = len(item['content']) if 'content' in item else 0
            if content_size > self.max_content_size:
                message = f"Content too large ({content_size} bytes) for {item['url']}, truncating"
                self.logger.warning(message)
                spider.logger.warning(message)
                # Truncate content to max size
                item['content'] = item['content'][:self.max_content_size] + "\n<!-- Content truncated due to size -->"
            
            # Generate a base filename from the URL
            base_filename = self.get_filename_from_url(item['url'])
            
            # Save the clean HTML content to a file - use buffered writing
            html_filename = f"{base_filename}.html"
            html_filepath = os.path.join(self.html_dir, html_filename)
            
            with open(html_filepath, 'w', encoding='utf-8', buffering=1024*8) as f:
                f.write(item['content'])
            
            # Prepare data for JSON - don't duplicate the full HTML
            json_data = dict(item)
            # We don't need to duplicate the full HTML in JSON
            json_data['content'] = "See HTML file for full content"
            
            # Save JSON data - use buffered writing
            json_filename = f"{base_filename}.json"
            json_filepath = os.path.join(self.json_dir, json_filename)
            
            with open(json_filepath, 'w', encoding='utf-8', buffering=1024*8) as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            spider.logger.info(f"Saved HTML to {html_filepath}")
            spider.logger.info(f"Saved JSON to {json_filepath}")
            
            return item
            
        except Exception as e:
            # Log error and drop item on failure
            error_msg = f"Error processing item from {item.get('url', 'unknown URL')}: {str(e)}"
            self.logger.error(error_msg)
            spider.logger.error(error_msg)
            raise DropItem(error_msg)
