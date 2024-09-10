import scrapy
from newspaper_scraper.items import NewspaperItem

class AismileySpiderSpider(scrapy.Spider):
    name = "aismiley_spider"
    allowed_domains = ["aismiley.co.jp"]
    start_urls = ["https://aismiley.co.jp/ai_news/"]
    
    def __init__(self, *args, **kwargs):
        super(AismileySpiderSpider, self).__init__(*args, **kwargs)
        self.article_count = 0
        self.article_limit = 20

    def parse(self, response):
        article_links = response.xpath('//*[@id="top"]/main/div[3]/div[1]/div[1]/article')
        for link in article_links:
            if self.article_count >= self.article_limit:
                return  # Stop crawling if we've reached the limit
            yield scrapy.Request(url=link.css('a').css('::attr(href)').get(), callback=self.parse_article)
        
        if self.article_count < self.article_limit:
            next_page = response.css('[rel="next"] ::attr(href)').get()
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse)    
    
    def parse_article(self, response):
        if self.article_count >= self.article_limit:
            return  # Stop parsing if we've reached the limit

        newspaper_item = NewspaperItem()
        combined_string = ''.join(response.xpath('//*[@class="container"]/p[not(@class="date")]/text()').getall()).replace('\n','')
        newspaper_item['source'] = "aismiley"
        newspaper_item['link'] = response.url
        newspaper_item['title'] = response.xpath('//*[@class="container"]/h1/span/text()').get()
        newspaper_item['time'] = response.css('p.date::text').get().replace('最終更新日:','')
        newspaper_item['tag'] = response.xpath('//*[@class="aiNewsArticle__detail aiNewsArticle__detail--single"]/dl[1]/dd/a/text()').getall()
        newspaper_item['content'] = combined_string
        
        self.article_count += 1
        yield newspaper_item