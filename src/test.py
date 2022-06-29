import re
import time
from pprint import pp
import requests
import ast
import json
import validators
import tldextract
from user_agent import generate_user_agent
from bs4 import BeautifulSoup

from dateutil.parser import parse

def scrape(url:str, wait_time:int=5):

    # check for script type: application/ld+json

    def is_date(string, fuzzy=False):
        try: 
            parse(string, fuzzy=fuzzy)
            return True
        except ValueError:
            return False

    def get_schema_json(soup: BeautifulSoup):
        script_text = soup.find('script', attrs={'type': 'application/ld+json'})
        return json.loads(script_text.text) if script_text else None

    def get_author(soup: BeautifulSoup, schema:dict={}, 
                    tags:list=['meta','a','div','span', 'p', 'li'], 
                    attributes:list=['name', 'itemprop', 'href', 'class']):
        
        schema = {} if not schema else schema
        author = schema.get('author')
        if author:
            if isinstance(author, list):
                return author[0].get('name')
            return author.get('name')
        result = []
        for attribute in attributes:
            author = [soup.find(tag, attrs={attribute: re.compile(r"author")}) for tag in tags]
            x = [item.text for item in author if item != None and item.text != "" and item.text not in result and len(item.text.split(' ')) <= 10]
            if len(x) > 0:
                result.append(",".join(x))
        result = ", ".join(result) if len(result) > 0 else None
        return result
    
    def get_keywords(soup: BeautifulSoup):
        return soup.find('meta', attrs={'name': 'keywords'})
    
    def get_publish_date(soup: BeautifulSoup, schema:dict={}):
        schema = {} if not schema else schema
        date = schema.get('datePublished')
        if date:
            return date
        
        date = soup.find('meta', attrs={'property': 'article:published_time'})
        if date:
            return date.get('content')
        
        date = soup.find('time')
        if date:
            return date.get('datetime')
        
        date = []
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
            for tag_element in soup.find_all(tag):
                if is_date(tag_element.text):
                    cleaned_text = re.sub(r'\n', '', tag_element.text)
                    cleaned_text = re.sub(' +', '', cleaned_text)
                    date.append(cleaned_text)
        return date
    
    def get_image(soup: BeautifulSoup):
        image = soup.find('meta', attrs={"property": "og:image"})
        if not image:
            image = soup.find('meta', attrs={'name':'image'})
        image = image['content'] if image else None
        return image

    def get_description(soup: BeautifulSoup):
        description = soup.find('meta', attrs={"property": "og:description"})
        if not description:
            description = soup.find('meta', attrs={"name": "description"})
        description = description['content'] if description else None
        return description
    
    def get_canonical_url(soup: BeautifulSoup):
        canonical_url = soup.find('link', attrs={'rel': "canonical"})
        canonical_url = canonical_url['href'] if canonical_url else None
        return canonical_url
        
    
    if not validators.url(url):
        print('Not a valid URL\nPlease provide a valid URL')
        return None

    time.sleep(wait_time)
    content = requests.get(url, headers={'User-Agent': generate_user_agent()})
    html_content = content.text
    soup = BeautifulSoup(html_content, 'html.parser')
    domain_extract = tldextract.extract(url)
    content_schema = get_schema_json(soup=soup)

    data = {
        'article_title': soup.find('title').text,
        'description': get_description(soup=soup),
        'article_content': None,
        'author': get_author(soup=soup, schema=content_schema),
        'publish_date': get_publish_date(soup=soup, schema=content_schema),
        'article_url': url,
        'canonical_url': get_canonical_url(soup=soup),
        'publisher_name': domain_extract.domain.capitalize(),
        'image': get_image(soup=soup),
        'video_url': None,
        'audio_url': None,
    }
    return data


if __name__ == '__main__':
    url = 'https://www.financialexpress.com/market/lic-tata-steel-among-139-stocks-to-hit-52-week-low-on-bse-37-scrips-at-fresh-highs/2559941/'
    x = scrape(url)
    pp(x)


