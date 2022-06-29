# Article Scraper Code
import re
import json
import time
import logging
import requests
import tldextract
import validators
from pprint import pp
from typing import Union
# from rake_nltk import Rake
from bs4 import BeautifulSoup
from dateutil.parser import parse
from user_agent import generate_user_agent

logging.basicConfig(level=logging.INFO)

class ArticleScraper:
    def __init__(self, wait_time:int) -> None:
        """
        Description: Scraper class to extract article content from given URL
        Input: 
            > article_url: str => url of the article to scrape
            > wait_time: int => time in seconds to wait before extracting content
        """
        self.__url = None
        self.__wait_time = wait_time
        self.__html_content = None
        self.__soup = None
        self.__schema = {}
        self.__article_content = None
        self.__domain_extract = None
    
    def __get_schema_json(self) -> None:
        # check for script type: application/ld+json
        script_text = self.__soup.find('script', attrs={'type': 'application/ld+json'})
        self.__schema = json.loads(script_text.text, strict=False) if script_text else {}
        if isinstance(self.__schema, list):
            for item in self.__schema:
                if item.get('@type'):
                    if 'article' in item.get('@type').lower():
                        self.__schema = item
                        break
    
    # def __get_full_schema_json(self) -> None:
    #     # check for script type: application/ld+json
    #     script_text = self.__soup.find('script', attrs={'type': 'application/ld+json'})
    #     self.__schema = json.loads(script_text.text, strict=False) if script_text else {}
    #     return self.__schema

    def __get_publisher(self):
        publisher = self.__schema.get('publisher')
        if publisher:
            return publisher.get('name')
        else:
            return self.__domain_extract.domain.capitalize()
    
    def __get_title(self):
        title = self.__soup.find('title').text
        return re.sub(r'\n', '', title)

    def __get_author(self,
                    tags:list=['meta','a','div','span', 'p', 'li'], 
                    attributes:list=['name', 'itemprop', 'href', 'class']):
        author = self.__schema.get('author')
        if author:
            if isinstance(author, list):
                return author[0].get('name')
            if isinstance(author, str):
                return author
            return author.get('name')
        
        graph = self.__schema.get('@graph')
        if graph:
            x = [item.get('name') for item in graph if item.get('@type') == 'Person']
            if len(x) > 0:
                return x[0]
        
        result = []
        for attribute in attributes:
            author = [self.__soup.find(tag, attrs={attribute: re.compile(r"author")}) for tag in tags]
            x = [item.text for item in author if item != None and item.text != "" and item.text not in result and len(item.text.split(' ')) <= 10]
            if len(x) > 0:
                result.append(",".join(x))
        result = ", ".join(list(set(result))) if len(result) > 0 else None
        return ArticleScraper.text_cleaning(result)
        
    def __get_keywords(self, attributes=['name', 'property']):
        x = [self.__soup.find('meta', attrs={attribute: re.compile(r"keyword")}) for attribute in attributes]
        x = ", ".join([item.get('content') for item in x if item != None])
        # if len(x.split(',')) <= 1 and self.__article_content:
        #     r = Rake()
        #     r.extract_keywords_from_text(self.__article_content)
        #     x = r.get_ranked_phrases()
        return x
        
    def __get_publish_date(self):
        date = self.__schema.get('datePublished')
        if date:
            return date
        
        date = self.__soup.find('meta', attrs={'property': 'article:published_time'})
        if date:
            return date.get('content')
        
        date = self.__soup.find('time')
        if date:
            return date.get('datetime')
        
        date = []
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'li']:
            for tag_element in self.__soup.find_all(tag):
                if ArticleScraper.is_date(tag_element.text):
                    date_extracted = ArticleScraper.text_cleaning(tag_element.text)
                    if len(date_extracted) <= 2:
                        continue
                    date.append(date_extracted)
        date = date if len(date) > 0 else None
        return date


    def __get_image(self):
        attributes = ['property', 'name']
        image = [self.__soup.find('meta', attrs={attribute: re.compile(r"image")}) for attribute in attributes]
        image = ", ".join(list(set([item.get('content') for item in image if item != None])))
        return image

    def __get_description(self):
        attributes = ['property', 'name']
        description = [self.__soup.find('meta', attrs={attribute: re.compile(r"description")}) for attribute in attributes]
        description = [item.get('content') for item in description if item != None][0]
        return description

    def __get_canonical_url(self):
        canonical_url = self.__soup.find('link', attrs={'rel': "canonical"})
        canonical_url = canonical_url['href'] if canonical_url else None
        return canonical_url

    def __get_content(self, 
                      tags:list=['article', 'section', 'main'],
                      tags_to_remove:list=['style', 'script']):
        
        content = []
        temp_soup = BeautifulSoup(self.__html_content, 'html.parser')

        for tag in tags_to_remove:
            for s in temp_soup.select(tag):
                s.extract()
        
        for tag in tags:
            if temp_soup.find(tag):
                text = ",".join([item.get_text() for item in temp_soup.find_all(tag)])
                content.append(text)
        max_len, max_index = 0, 0
        for index, item in enumerate(content):
            content_cleaned = ArticleScraper.text_cleaning(item)
            if len(content_cleaned) > max_len:
                max_len = len(content_cleaned)
                max_index = index
        
        content = ArticleScraper.text_cleaning(content[max_index]) if len(content) > 0 else None

        if not content:
            # If None Do this
            content_class_names = ['content', 'blog', 'article']
            result = []
            for c_name in content_class_names:
                content_div = temp_soup.find('div', {'class': re.compile(r'{}'.format(c_name))})
                if content_div:
                    content_div.find_all("p", recursive=False)
                    x = [item.text for item in content_div if item != None]
                    if len(x) > 0:
                        result.append(x)
            content = "".join(result[0]) if len(result) > 0 else "".join(result)
        return content

    def __scrape_html(self) -> None:
        if self.__isvalid_url:
            time.sleep(self.__wait_time)
            content = requests.get(self.__url, headers={'User-Agent': generate_user_agent()})
            self.__html_content = content.text
            self.__soup = BeautifulSoup(self.__html_content, 'html.parser')
        else:
            logging.info(f'Not a valid URL\nPlease register a valid URL')
    
    def __extract_article_content(self) -> dict:
        self.__domain_extract = tldextract.extract(self.__url)
        self.__get_schema_json()

        data = {
            'article_title': self.__get_title(),
            'description': self.__get_description(),
            'article_content': self.__get_content(),
            'author': self.__get_author(),
            'publish_date': self.__get_publish_date(),
            'article_url': self.__url,
            'canonical_url': self.__get_canonical_url(),
            'publisher_name': self.__get_publisher(),
            'image': self.__get_image(),
            'keywords': self.__get_keywords(),
            'video_url': None,
            'audio_url': None,
        }
        return data

    def run(self, article_url:str) -> Union[dict, None]:
        self.__url = article_url
        self.__isvalid_url = validators.url(self.__url)
        extracted_info = None
        if self.__isvalid_url:
            logging.info(f'Scraping HTML Content')
            self.__scrape_html()
            if self.__html_content:
                logging.info(f'Scraping Completed')
                extracted_info = self.__extract_article_content()
            else:
                logging.info(f'Scraping Failed')
            return extracted_info
        else:
            return extracted_info
    
    @staticmethod
    def is_date(text, fuzzy=False):
        try:
            parse(text, fuzzy=fuzzy)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def text_cleaning(text, remove_keywords:Union[list, None]=None):
        if text:
            text = re.sub(r'\n', ' ', text)
            text = re.sub(r'\t', '', text)
            text = re.sub(' +', ' ', text)
            text = text.encode('ascii', 'ignore').decode()
            return text.strip()
        return text


if __name__ == "__main__":
    url = 'https://www.financialexpress.com/market/cafeinvest/buy-bpcl-sbi-life-hcl-tech-jsw-steel-charts-show-gains-in-near-term-nifty-above-15750-could-reclaim-16000/2576173/'
    scraper = ArticleScraper(wait_time=5)
    html = scraper.run(article_url=url)
    pp(html)