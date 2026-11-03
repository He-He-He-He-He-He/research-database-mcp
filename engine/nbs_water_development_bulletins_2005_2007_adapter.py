"""NBS publication of MWR national water development bulletins for 2005 and 2007."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2005: 'https://www.stats.gov.cn/sj/tjgb/qttjgb/qgqttjgb/202302/t20230218_1913264.html', 2007: 'https://www.stats.gov.cn/sj/tjgb/qttjgb/qgqttjgb/202302/t20230218_1913278.html'}

def catalog():
    return [{'year': y, 'url': u, 'title': f'{y}年全国水利发展统计公报'} for y, u in SOURCES.items()]

def search(year, keyword='', limit=50, offset=0):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2005 or 2007')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 200) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    url = SOURCES[year]
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    content = soup.select_one('.detail-text-content.mhide .txt-content')
    if not content:
        raise ValueError('official bulletin content unavailable')
    texts = [' '.join(p.get_text(' ', strip=True).split()) for p in content.select('p') if not p.find('p')]
    texts = [x for x in texts if x]
    if len(texts) < 10 or not any(('水利' in x for x in texts)):
        raise ValueError('unexpected bulletin content')
    q = ''.join(keyword.split())
    matches = [{'paragraph': i, 'text': v} for i, v in enumerate(texts, 1) if q in ''.join(v.split())]
    return {'year': year, 'title': f'{year}年全国水利发展统计公报', 'url': url, 'source': '水利部公报，由国家统计局转载', 'paragraph_count': len(texts), 'matched': len(matches), 'offset': offset, 'paragraphs': matches[offset:offset + limit], 'truncated': len(matches) > offset + limit, 'note': '返回公报原文段落，不自动解析数字或表格；单位、统计范围及指标解释以原文为准。'}
