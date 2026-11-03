"""Historical national MOHRSS statistical bulletins, republished by CAOSS."""
import release_runtime
import requests
import fitz
from bs4 import BeautifulSoup
SOURCES = {2008: ('html', 'https://www.caoss.org.cn/news/html?id=11840'), 2010: ('html', 'https://www.caoss.org.cn/news/html?id=11842'), 2011: ('html', 'https://www.caoss.org.cn/news/html?id=11843'), 2015: ('html', 'https://www.caoss.org.cn/news/html?id=11846'), 2016: ('pdf', 'https://www.caoss.org.cn/UploadFile/news/file/20171111/20171111084220092009.pdf'), 2019: ('html', 'https://www.caoss.org.cn/news/html?id=11857'), 2021: ('pdf', 'https://www.caoss.org.cn/UploadFile/news/file/20220607/20220607161666106610.pdf'), 2022: ('pdf', 'https://www.caoss.org.cn/upload/file/23081713343321.pdf')}

def catalog():
    return [{'year': y, 'format': v[0], 'url': v[1], 'author': '人力资源和社会保障部', 'publisher': '中国社会保障学会转载'} for y, v in sorted(SOURCES.items())]

def search(year, keyword='', limit=20):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('年份未收录，不代表公报不存在')
    if not 1 <= int(limit) <= 200:
        raise ValueError('limit 必须在 1 至 200 之间')
    kind, url = SOURCES[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if kind == 'pdf':
        if not r.content.startswith(b'%PDF-'):
            raise RuntimeError('响应并非 PDF')
        doc = fitz.open(stream=r.content, filetype='pdf')
        items = [{'page': i + 1, 'text': page.get_text().strip()} for i, page in enumerate(doc)]
        doc.close()
    else:
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        body = soup.select_one('.news-det')
        if body is None:
            raise RuntimeError('正文缺失，来源可能改版')
        items = [{'paragraph': i + 1, 'text': p.get_text(' ', strip=True)} for i, p in enumerate(body.find_all('p')) if p.get_text(strip=True)]
    items = [item for item in items if keyword in item['text']]
    return {'year': year, 'url': url, 'author': '人力资源和社会保障部', 'publisher': '中国社会保障学会转载', 'format': kind, 'keyword': keyword, 'matches': len(items), 'results': items[:int(limit)], 'note': 'PDF 为页级检索；图表图片不作 OCR，跨年比较须核对统计口径与脚注。'}
