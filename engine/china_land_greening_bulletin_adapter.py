"""国家林业和草原局中国国土绿化状况公报（网页正文段落检索）。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2022: 'https://www.forestry.gov.cn/main/6246/20230314/164636667716389.html', 2023: 'https://www.forestry.gov.cn/c/www/gtlhbg/550046.jhtml', 2024: 'https://www.forestry.gov.cn/c/www/gtlhbg/621668.jhtml', 2025: 'https://www.forestry.gov.cn/lyj/1/lcdt/20260312/662822.html'}

def catalog():
    return [{'year': year, 'title': f'{year}年中国国土绿化状况公报', 'url': url} for year, url in URLS.items()]

def query(year, keyword='', offset=0, limit=20):
    if isinstance(year, bool) or not isinstance(year, int) or year not in URLS:
        raise ValueError('year 须为2022至2025')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为不超过100字的字符串')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('offset 须非负、limit 须为1至100')
    url = URLS[year]
    with requests.get(url, stream=True, allow_redirects=False, timeout=(12, 25)) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise RuntimeError('官网页面发生重定向')
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 3000000:
                raise RuntimeError('响应超过3MB')
            chunks.append(c)
    s = BeautifulSoup(b''.join(chunks).decode('utf-8'), 'html.parser')
    p = s.select_one('#zoomit')
    if not p:
        raise RuntimeError('官网正文结构已变化')
    lines = [x.get_text(' ', strip=True) for x in p.find_all(['p', 'h1', 'h2', 'h3', 'h4'], recursive=True) if x.get_text(' ', strip=True)]
    if len(lines) < 5 or not any((str(year) in x for x in lines[:5])):
        raise RuntimeError('公报年份或正文不符')
    rows = [{'paragraph_index': i + 1, 'text': x} for i, x in enumerate(lines) if not keyword or keyword.casefold() in x.casefold()]
    return {'source': '全国绿化委员会办公室，国家林业和草原局官网', 'year': year, 'url': url, 'keyword': keyword, 'total_paragraphs': len(lines), 'matched_paragraphs': len(rows), 'offset': offset, 'limit': limit, 'items': rows[offset:offset + limit], 'note': '年度公报正文段落本地包含检索；数字及口径按原文解释，部分段落涉及预测、计划或不同年份，不能将整段数字自动当成当年统计。仅 HTML 文字，不涵盖图片或附件。'}
