# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import sqlite3
from itemadapter import ItemAdapter


class NewspaperScraperPipeline:
    def process_item(self, item, spider):
        return item

class SqlitePipeline:
    def __init__(self):
        self.create_connection()
        self.create_table()

    def create_connection(self):
        database_path = os.getenv('DATABASE_PATH', '/app/data/content.db')
        self.conn = sqlite3.connect(database_path)
        self.curr = self.conn.cursor()

    def create_table(self):
        self.curr.execute("""CREATE TABLE IF NOT EXISTS articles
                        (id INTEGER PRIMARY KEY, source TEXT, link TEXT, title TEXT, 
                         time TEXT, tags TEXT, content TEXT, score REAL, summary TEXT)""")

    def process_item(self, item, spider):
        self.curr.execute("SELECT * FROM articles WHERE link = ?", (item['link'],))
        result = self.curr.fetchone()
        if result:
            spider.logger.warn(f"Item already in database: {item['link']}")
        else:
            self.curr.execute("""INSERT INTO articles (source, link, title, time, tags, content, score, summary)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                              (item['source'], item['link'], item['title'], item['time'], 
                               ','.join(item['tag']), item['content'], None, None))
            self.conn.commit()

        return item
