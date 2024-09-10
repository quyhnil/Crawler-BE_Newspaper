import scrapy
from newspaper_scraper.items import NewspaperItem

class AinowSpiderSpider(scrapy.Spider):
    name = "ainow_spider"
    allowed_domains = ["ainow.ai"]
    start_urls = ["https://ainow.ai/new"]
    
    def __init__(self, *args, **kwargs):
        super(AinowSpiderSpider, self).__init__(*args, **kwargs)
        self.article_count = 0
        self.article_limit = 20

    def parse(self, response):
        article_links = response.xpath('//*[@class="article_link"]/@href').getall()
        for link in article_links:
            if self.article_count >= self.article_limit:
                return  # Stop crawling if we've reached the limit
            yield scrapy.Request(url=link, callback=self.parse_article)
        
        if self.article_count < self.article_limit:
            next_page = response.xpath('//*[@class="next"]/@href').get()
            if next_page:
                yield response.follow(next_page, callback=self.parse)

    def parse_article(self, response):
        if self.article_count >= self.article_limit:
            return  # Stop parsing if we've reached the limit

        newspaper_item = NewspaperItem()
        combined_string = ''.join(response.xpath('//div[@class="entry-content"]//text()').getall()).replace('\n','')
        tags = response.xpath('//*[@class="article_area_data"][1]/span/a/text()').getall()
        cleaned_tags = [tag.replace('#', '') for tag in tags]
        newspaper_item['source'] = "ainow"
        newspaper_item['link'] = response.url
        newspaper_item['title'] =  response.xpath('//*[@class="article_main_title"]/text()').get()
        newspaper_item['time'] =  response.xpath('//*[@class="article_area_date"]/text()').get().replace('.','/')
        newspaper_item['tag'] =  cleaned_tags
        newspaper_item['content'] =  combined_string
        
        self.article_count += 1
        yield newspaper_item