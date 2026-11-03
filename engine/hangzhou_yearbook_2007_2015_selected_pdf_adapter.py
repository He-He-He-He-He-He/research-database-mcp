"""Selected official Hangzhou yearbook PDFs, edition 2007–2009 and 2012–2015."""
import release_runtime
import requests
YEARS = (2007, 2008, 2009, 2012, 2013, 2014, 2015)
CHAPTERS = {1: '综合', 2: '人口和就业人员'}

def catalog(year, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in YEARS:
        raise ValueError('available editions: 2007–2009 and 2012–2015')
    return [{'edition': year, 'chapter': n, 'title': title, 'source': f'杭州市统计局《杭州统计年鉴{year}》', 'url': f'https://tjj.hangzhou.gov.cn/tjnj/nj{year}/{n}.pdf'} for n, title in CHAPTERS.items() if keyword in title]

def chapter(year, number):
    if isinstance(number, bool) or not isinstance(number, int) or number not in CHAPTERS:
        raise ValueError('supported chapter numbers: 1 and 2')
    item = catalog(year)[number - 1]
    r = requests.get(item['url'], timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {**item, 'content_type': 'application/pdf', 'content': r.content}
