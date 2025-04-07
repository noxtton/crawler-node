import scrapy


class WebsiteItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()  # This will store the clean HTML
    text_content = scrapy.Field()  # This will store extracted text
    external_links = scrapy.Field()
    internal_links = scrapy.Field()
    timestamp = scrapy.Field()
