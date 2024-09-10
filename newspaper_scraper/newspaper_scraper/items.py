# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy



class NewspaperScraperItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    pass

class NewspaperItem(scrapy.Item):
    source = scrapy.Field()
    link = scrapy.Field()
    title = scrapy.Field()
    time = scrapy.Field()
    tag = scrapy.Field()
    content = scrapy.Field()