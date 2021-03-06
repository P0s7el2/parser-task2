import requests
import asyncio
from bs4 import BeautifulSoup
from time import time
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import aiohttp
import os

Base = declarative_base()


# orm-классы
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)

    def __init__(self, name, url):
        self.name = name
        self.url = url

    def __repr__(self):
        return "<User(name: '%s', url: '%s'>" % (self.name, self.url)


def start_db():
    # устанавливаем соединение с бд
    engine = create_engine('postgresql://postgres:1@localhost:5432/demo_facebook')
    # инициализируем сесисю
    Session = sessionmaker(bind=engine)
    session = Session()
    # создаем таблицу
    metadata = MetaData()
    # удаляем данные из таблиц
    # User.__table__.drop(engine)
    users_table = Table('users', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('name', String),
                        Column('url', String)
                        )
    metadata.create_all(engine)
    # определяем новый класс, от которого будет унаслед ORM-класс
    return session


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()


def get_users(html):
    """
   Return links
   :param html: str, html code of page
   :return: array of links
   """
    try:
        # парсим код
        soup = BeautifulSoup(html, 'lxml')
        # ищем элемент который содержит ссылки, потом ищем сами ссылки
        links = soup.find('div', class_='fbDirectoryBox mtm direct_listing').findAll('a', href=True)
        print(links)
        # проходимся по найденным эл и находим там url и название,
        # вставляем в массив
        info = []

        for a in links:
            url = a['href']
            title = a.get_text()
            # формируем словарь с сылками
            info.append([url, title])
        return info
    except AttributeError:
        print('error')


def set_links_to_db(links, session):
    # добавляем пользователей
    print(links)
    for item in links:
        url = item[0]
        name = item[1]
        session.add(User(name, url))
    # комитим
    session.commit()


def get_url_text(url):
    res = requests.get(url)
    return res.text


def main():
    tic = time()
    domain = 'http://test-pages:81/'
    # получаем все ссылки на сборки, в будущем может быть get_html
    for file in os.listdir("Users_pages"):
        if file.endswith(".html") and len(file) > 5:
            print(domain + file)
            links = get_users(get_url_text(f'{domain}{file}'))
    # открываем ссесию
    #links = get_users(get_url_text(domain + '/Baba%20Alinko%20Hausa%20_%20Baba%20Aliou%20Sow%20_%20People%20Directory.html'))
    if links:
        session = start_db()
        set_links_to_db(links, session)
    toc = time()

    print(toc - tic)


if __name__ == '__main__':
    main()
