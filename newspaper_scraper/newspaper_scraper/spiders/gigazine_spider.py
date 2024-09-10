import scrapy
from newspaper_scraper.items import NewspaperItem
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dateutil import parser


genai.configure(api_key="AIzaSyA-KWJHCEmG9KWCmtn41w8oL01Rm3nwdkI")


generation_config = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 256,
    "response_mime_type": "text/plain",
}

model_ai_relevance = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=(
        'あなたの仕事は、与えられたタイトルが人工知能（AI）に関連しているかどうかを判断することです。'
        'タイトルがAIに関連している場合は「1」、関連していない場合は「0」と応答してください。'
        '複数のタイトルが与えられた場合は、それぞれのタイトルに対して0か1を返し、カンマで区切ってください。'
    ),
)

chat_session_relevance = model_ai_relevance.start_chat(history=[])

class GigazineSpiderSpider(scrapy.Spider):
    name = "gigazine_spider"
    allowed_domains = ["gigazine.net"]
    start_urls = ["https://gigazine.net"]

    def parse(self, response):
        article_links = response.xpath('//*[@class="card"]/h2/a')
        titles = []
        links = []

        for link in article_links:
            title = link.css('span::text').get()
            href = link.xpath('@href').get()
            if title and href:
                titles.append(title)
                links.append(href)

        batch_size = 40
        for i in range(0, len(titles), batch_size):
            title_batch = titles[i:i+batch_size]
            link_batch = links[i:i+batch_size]
            
            prompt = f"以下のニュースタイトルがAIに関連しているかどうかを判断し、関連している場合は1、関連していない場合は0で回答してください。回答はカンマで区切ってください。タイトル: {', '.join(title_batch)}"
            relevance_response = chat_session_relevance.send_message(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                }
            ).text
        ai_related_titles = []
        ai_related_links = []
        relevance_results = relevance_response.strip().split(',')
        for title, link, classification in zip(title_batch, link_batch, relevance_results):
            if classification.strip() == "1":
                ai_related_titles.append(title)
                ai_related_links.append(link)

            if ai_related_titles: 
                for title, link in zip(ai_related_titles, ai_related_links):
                    yield scrapy.Request(url=link, callback=self.parse_article)

        next_page = response.xpath('//*[@id="nextpage"]/a').xpath('@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_article(self, response):
        newspaper_item = NewspaperItem()
        combined_string = ''.join(response.xpath('//*[@class="preface"]/text()').getall()).replace('\n', '')
        newspaper_item['source'] = "gigazine"
        newspaper_item['link'] = response.url
        newspaper_item['title'] = response.css('h1::text').get().replace('\n', '').replace('\n    ', '')
        original_time = response.xpath('//time/@datetime').get()
        if original_time:
            parsed_time = parser.parse(original_time)
            formatted_time = parsed_time.strftime('%Y/%m/%d')
            newspaper_item['time'] = formatted_time
        newspaper_item['content'] = combined_string
        newspaper_item['tag'] = "null"

        yield newspaper_item