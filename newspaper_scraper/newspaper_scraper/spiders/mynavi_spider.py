import scrapy
from newspaper_scraper.items import NewspaperItem
from dateutil import parser

class MynaviSpiderSpider(scrapy.Spider):
    name = "mynavi_spider"
    allowed_domains = ["news.mynavi.jp"]
    start_urls = ["https://news.mynavi.jp/techplus/tag/artificial_intelligence/"]

    def __init__(self, *args, **kwargs):
        super(MynaviSpiderSpider, self).__init__(*args, **kwargs)
        self.article_count = 0
        self.article_limit = 20

    def parse(self, response):
        article_links = response.css('li.c-archiveList_listNode')
        for link in article_links:
            if self.article_count >= self.article_limit:
                return  # Stop crawling if we've reached the limit
            yield scrapy.Request(url="https://news.mynavi.jp/" + link.css('a.c-archiveList_listNode_link').css('::attr(href)').get(), callback=self.parse_article)  

        if self.article_count < self.article_limit:
            next_page = response.css('[rel="next"] ::attr(href)').get()
            if next_page is not None:
                next_page_url = 'https://news.mynavi.jp/techplus' + next_page
                yield response.follow(next_page_url, callback=self.parse)

    def parse_article(self, response):
        if self.article_count >= self.article_limit:
            return  # Stop parsing if we've reached the limit

        newspaper_item = NewspaperItem()
        tag = response.xpath('//*[@class="articleRelated_keywordList"]/li/a/text()').getall()
        combined_string = ''.join(response.xpath('//*[@id="js-articleBody"]/p/text()').getall()).replace('\n','')
        newspaper_item['source'] = "mynavi"   
        newspaper_item['link'] = response.url
        newspaper_item['title'] = response.css('h1::text').get().replace('\n','').replace('\n    ','')
        original_time = response.xpath('//time/@datetime').get()
        if original_time:
            parsed_time = parser.parse(original_time)
            formatted_time = parsed_time.strftime('%Y/%m/%d')
            newspaper_item['time'] = formatted_time
        newspaper_item['tag'] =  tag[:len(tag) // 2]
        newspaper_item['content'] =  combined_string
        
        self.article_count += 1
        yield newspaper_item