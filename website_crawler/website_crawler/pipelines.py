import json
import os
from datetime import datetime


class WebsiteCrawlerPipeline:
    def __init__(self):
        # Create output directory if it doesn't exist
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def process_item(self, item, spider):
        # Create a filename based on the URL and timestamp
        filename = f"{item['url'].replace('://', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)

        # Convert item to dictionary and write to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dict(item), f, ensure_ascii=False, indent=2)

        return item
