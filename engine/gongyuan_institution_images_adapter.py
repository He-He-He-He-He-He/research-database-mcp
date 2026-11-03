"""公元集成教学图片库校内许可会话：图片题录和文字说明，不下载图片。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'http://10.15.61.245:81/'

def _html(r):
    r.raise_for_status()
    r.encoding = 'gb18030'
    return BeautifulSoup(r.text, 'html.parser')

def _session():
    s = requests.Session()
    p = _html(s.get(BASE + 'reveal.php', timeout=20))
    if '授权给“ 浙江大学 ”使用' not in p.get_text(' ', strip=True):
        s.close()
        raise RuntimeError('未确认浙江大学机构与许可页面')
    r = s.post(BASE + 'reveal.php', data={'re': '  同意  '.encode('gb2312')}, timeout=20)
    r.raise_for_status()
    p = _html(s.get(BASE + 'class.php', timeout=20))
    if not p.title or '授权给： 浙江大学使用' not in p.title.get_text(' ', strip=True):
        s.close()
        raise RuntimeError('未进入浙江大学机构会话')
    return s

def search(keyword, page=1):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    q = keyword.strip()
    with _session() as s:
        p = _html(s.post(BASE + 'search_content.php', data={'Keyword1': q, 'type': 'quick', 'page': page}, timeout=30))
    text = p.get_text(' ', strip=True)
    m = re.search('共\\s*(\\d+)\\s*项\\s*(\\d+)\\s*页', text)
    if not m or q not in text:
        raise RuntimeError('未确认检索词或结果总数')
    items = []
    for img in p.select('img[src^="thumbnail.php?Id="]'):
        match = re.fullmatch('thumbnail\\.php\\?Id=(\\d+)', img.get('src', ''))
        box = img.find_parent('table')
        box = box.find_parent('table') if box else None
        if not match or not box:
            raise RuntimeError('图片题录结构异常')
        caption = box.select_one('font.f')
        items.append({'id': match.group(1), 'caption_excerpt': caption.get_text(' ', strip=True) if caption else None})
    if len(items) > 12 or (int(m.group(1)) > 0 and page <= int(m.group(2)) and (not items)):
        raise RuntimeError('图片题录数量异常')
    return {'source': '公元集成教学图片数据库', 'institution': '浙江大学', 'query': q, 'page': page, 'total': int(m.group(1)), 'pages': int(m.group(2)), 'items': items, 'note': '校园内网 HTTP；按已同意的机构许可单次搜索，只返回图片编号和可能截断的说明，不下载图片。'}

def detail(image_id):
    if isinstance(image_id, bool) or not re.fullmatch('[0-9]{1,20}', str(image_id)):
        raise ValueError('图片编号无效')
    image_id = str(image_id)
    with _session() as s:
        p = _html(s.post(BASE + 'image_content.php', data={'id': image_id, 'type': 'detail'}, timeout=20))
    text = p.get_text(' ', strip=True)
    if not re.search('图片编号\\s*[:：]\\s*' + re.escape(image_id) + '(?:\\s|$)', text):
        raise RuntimeError('站方详情编号不匹配')
    return {'source': '公元集成教学图片数据库', 'institution': '浙江大学', 'id': image_id, 'detail_text': text, 'note': '校园内网 HTTP；原站图片详情文字，未下载图片；图片使用范围以机构许可为准。'}
