import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from newspaper_scraper.spiders.ainow_spider import AinowSpiderSpider
from newspaper_scraper.spiders.aismiley_spider import AismileySpiderSpider
from newspaper_scraper.spiders.mynavi_spider import MynaviSpiderSpider

def run_spiders():
    settings = get_project_settings()

    process = CrawlerProcess(settings)

    process.crawl(AinowSpiderSpider)
    process.crawl(AismileySpiderSpider)
    process.crawl(MynaviSpiderSpider)

    process.start()

if __name__ == "__main__":
    run_spiders()