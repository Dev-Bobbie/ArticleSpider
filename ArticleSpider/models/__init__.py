from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String,DateTime
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from settings import MYSQL_HOST,MYSQL_DBNAME,MYSQL_USER,MYSQL_PASSWORD

engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DBNAME}?charset=utf8", max_overflow=5)
Base = declarative_base()

class Article(Base):
    __tablename__ = 'jobbole_article'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    create_date = Column(DateTime, nullable=True)
    url = Column(String(300), nullable=False)
    url_object_id = Column(String(50),nullable=False)
    front_image_url = Column(String(300),nullable=True)
    front_image_path = Column(String(200),nullable=True)
    comment_nums = Column(Integer, nullable=True)
    fav_nums = Column(Integer,nullable=True)
    praise_nums = Column(Integer, nullable=True)
    tags = Column(String(200),nullable=True)
    content = Column(LONGTEXT,nullable=True)

    __table_args__ = (
        {"mysql_engine": "InnoDB","mysql_charset": "utf8"}, # 表的引擎
    )


def is_database_exists():
    if not database_exists(engine.url):
        create_database(engine.url)
        return False
    return True

def create_all_table():
    # 创建所有表
    Base.metadata.create_all(engine)

def drop_all_table():
    # 删除所有表
    Base.metadata.drop_all(engine)

if __name__ == '__main__':
    create_all_table()
    # drop_all_table()