"""交通运输部民航统计目录分页及原始 PDF 按页检索。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urljoin, urlsplit
ROOT = 'https://www.mot.gov.cn/shuju/tongjishuju/minhang/'

def fetch(url):
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout

def list_page(page=1, keyword=''):
    if not isinstance(page, int) or not 1 <= page <= 10:
        raise ValueError('页码须在1至10之间（按目前目录范围）')
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError('目录解析需要 Beautiful Soup 4') from e
    page_url = ROOT + ('' if page == 1 else f'index_{page - 1}.html')
    s = BeautifulSoup(fetch(page_url), 'html.parser')
    nodes = s.select('.news-list-section .news-item')
    if not nodes:
        raise ValueError('目录未识别或无记录')
    rows = []
    for node in nodes:
        link = node.select_one('a.news-link')
        title = node.select_one('.news-title')
        date = node.select_one('.news-date')
        if link and title and (keyword in title.get_text(strip=True)):
            rows.append({'title': title.get_text(strip=True), 'date': date.get_text(strip=True) if date else None, 'url': urljoin(page_url, link.get('href', ''))})
    return {'source': page_url, 'page': page, 'keyword': keyword, 'items': rows, 'note': '关键词仅筛选指定页面；时间为发布日，不一定是统计月份。'}

def search_pdf(url, keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.mot.gov.cn' or (not re.fullmatch('/shuju/tongjishuju/minhang/\\d{6}/P\\d+\\.pdf', u.path)) or u.query or u.fragment:
        raise ValueError('只支持交通运输部民航统计目录下PDF')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('PDF检索需要 PyMuPDF') from e
    pages = []
    with fitz.open(stream=fetch(url), filetype='pdf') as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            if ''.join(keyword.split()) in ''.join(text.split()):
                pages.append({'pdf_page': i + 1, 'text': text})
    return {'source': url, 'keyword': keyword, 'pages': pages, 'note': '原PDF文字提取，未将单元格映射为结构化数值；图片未OCR。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    l = s.add_parser('list')
    l.add_argument('--page', type=int, default=1)
    l.add_argument('--keyword', default='')
    d = s.add_parser('search')
    d.add_argument('url')
    d.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(list_page(a.page, a.keyword) if a.cmd == 'list' else search_pdf(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
