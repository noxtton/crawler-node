import json
import os
from datetime import datetime
from urllib.parse import urlparse
import codecs


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
        # Generate a base filename from the URL
        base_filename = self.get_filename_from_url(item['url'])
        
        # Save the clean HTML content to a file
        html_filename = f"{base_filename}.html"
        html_filepath = os.path.join(self.html_dir, html_filename)
        
        with codecs.open(html_filepath, 'w', 'utf-8') as f:
            f.write(item['content'])
        
        # Prepare data for JSON
        json_data = dict(item)
        # We don't need to duplicate the full HTML in JSON
        json_data['content'] = "See HTML file for full content"
        
        # Save JSON data
        json_filename = f"{base_filename}.json"
        json_filepath = os.path.join(self.json_dir, json_filename)
        
        with codecs.open(json_filepath, 'w', 'utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"Saved HTML to {html_filepath}")
        spider.logger.info(f"Saved JSON to {json_filepath}")

        return item
