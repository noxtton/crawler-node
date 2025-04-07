import scrapy


class WebsiteItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    external_links = scrapy.Field()
    internal_links = scrapy.Field()
    timestamp = scrapy.Field()
