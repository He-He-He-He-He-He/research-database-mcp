"""China supply-and-marketing cooperative website article JSON read interface."""
import release_runtime
import requests
from bs4 import BeautifulSoup
API = 'https://api.chinacoop.gov.cn/api/getArticle'

def article(article_id):
    if isinstance(article_id, bool) or not isinstance(article_id, int) or article_id < 1:
        raise ValueError('article_id must be a positive integer')
    r = requests.get(API, params={'aid': article_id}, timeout=30, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    j = r.json()
    if j.get('fileID') != article_id or not isinstance(j.get('content'), str):
        raise ValueError('article unavailable or unexpected response')
    soup = BeautifulSoup(j['content'], 'html.parser')
    paragraphs = [p.get_text(' ', strip=True) for p in soup.select('p') if p.get_text(' ', strip=True)]
    return {'id': article_id, 'title': j.get('title'), 'source': j.get('source'), 'published': j.get('publishTime'), 'editor': j.get('editor'), 'page_url': f'https://www.chinacoop.gov.cn/news.html?aid={article_id}', 'html': j['content'], 'paragraphs': paragraphs}

def bulletin_2020(keyword=''):
    result = article(1711930)
    if keyword:
        result['paragraphs'] = [p for p in result['paragraphs'] if keyword.casefold() in p.casefold()]
    return result
