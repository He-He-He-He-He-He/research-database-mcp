"""中国边疆史地研究资料库 IP 机构详情与目录，不提取正文或图片。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from frontier_history_ip_catalog_adapter import BASE

def detail(record_id, expected_title, offset=0, limit=20):
    if not isinstance(record_id, str) or not re.fullmatch('\\d{1,15}', record_id):
        raise ValueError('文献编号须为 1–15 位数字')
    if not isinstance(expected_title, str) or not 1 <= len(expected_title.strip()) <= 200 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('请提供题录中完整的单行题名')
    if type(offset) is not int or not 0 <= offset <= 100000 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('offset 须为 0–100000，limit 须为 1–100')
    target = BASE + 'literature/' + record_id + '/'
    try:
        r = requests.get(target, timeout=25)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError('边疆史地详情请求失败：' + type(e).__name__) from None
    final = urlparse(r.url)
    if final.scheme != 'http' or final.hostname != '10.15.61.59' or final.port != 8080 or (final.path not in ('/literature/' + record_id + '/', '/literature/' + record_id + '/page/1/')) or final.query or final.fragment:
        raise RuntimeError('边疆史地详情地址与请求不一致')
    b = BeautifulSoup(r.content, 'html.parser')
    text = b.get_text(' ', strip=True)
    if not re.search('用[戶户]\\s*[：:]\\s*zjdx\\b', text, re.I):
        raise RuntimeError('未确认浙江大学机构账户')
    meta = b.select_one('#n1Tab_Content2')
    heading = meta.select_one('h3') if meta else None
    title = expected_title.strip()
    page_title = b.title.get_text(' ', strip=True) if b.title else ''
    if not heading or title not in heading.get_text(' ', strip=True) or (not page_title.startswith(title)):
        raise RuntimeError('详情题名与预期不符')
    metadata = [p.get_text(' ', strip=True) for p in meta.select('p') if p.get_text(' ', strip=True)]
    if not metadata:
        raise RuntimeError('详情书目信息缺失')
    selector = b.select_one('#selector .listbox')
    if not selector:
        raise RuntimeError('文献目录结构异常')
    chapters = []
    for a in selector.select('a[href]'):
        u = urlparse(urljoin(r.url, a.get('href', '')))
        m = re.fullmatch('/literature/' + re.escape(record_id) + '/chapter/(\\d{1,30})/', u.path)
        if u.scheme == 'http' and u.hostname == '10.15.61.59' and (u.port == 8080) and (not u.query) and (not u.fragment) and m:
            name = a.get_text(' ', strip=True)
            if name:
                chapters.append({'chapter_id': m.group(1), 'title_raw': name, 'url': BASE + 'literature/' + record_id + '/chapter/' + m.group(1) + '/'})
    if not chapters:
        raise RuntimeError('未识别任何文献目录项')
    options = b.select('#pages select option')
    if not options or any((not (x.get('value') or '').isdigit() or int(x['value']) != i + 1 for i, x in enumerate(options))):
        raise RuntimeError('原站页面序号列表异常')
    selected = [int(x['value']) for x in options if x.has_attr('selected')]
    if len(selected) != 1:
        raise RuntimeError('原站当前页面序号异常')
    return {'source': '中国边疆史地研究资料数据库', 'institution_marker': 'zjdx', 'record_id': record_id, 'expected_title': title, 'metadata_lines_raw': metadata, 'chapter_count': len(chapters), 'source_page_options_count': len(options), 'source_selected_page': selected[0], 'offset': offset, 'items': chapters[offset:offset + limit], 'note': '站方书目信息及页面目录，按原站顺序保留；目录项可能是封面、序或页，不等同独立章节。页面选项数量与序号来自原站控件，不等同印刷页码。未提取正文、图片或核验逐项阅读权限。校园内网 HTTP 明文，请勿输入敏感信息。'}
