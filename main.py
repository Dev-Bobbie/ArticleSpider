from scrapy.cmdline import execute
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ArticleSpider.models import create_all_table,is_database_exists

if not is_database_exists():
    create_all_table()
execute("scrapy crawl jobbole".split())