"""上海人大法规数据库：地方性法规及市法院、检察院规范文件分类。"""
import release_runtime
import re
from urllib.parse import urlencode, urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://fgk.shrd.gov.cn'
CATEGORIES = {'local': 'dfxfg', 'court': 'sgygfxwj', 'procuratorate': 'sjcygfxwj'}
VERSION_FORMS = {'新制定': '2c909de7652191f701652199ee2f000f', '修改': '2c909de7652191f70165219a0e600011', '失效': '2c90a4826652b836016652bd05990003', '废止': '2c909de7652191f70165219a3fa60013'}

def shanghai_law_category_search(query='', category='local', version_form=None, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    if category not in CATEGORIES:
        raise ValueError('category 须为 local、court 或 procuratorate')
    if version_form is not None and version_form not in VERSION_FORMS:
        raise ValueError('版本形式须为新制定、修改、失效或废止')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or not 1 <= page <= 100 or (not 1 <= page_size <= 50):
        raise ValueError('页码须为 1–100、每页 1–50 条')
    typ = CATEGORIES[category]
    p = {'pageNo': page, 'pageSize': page_size, 'isLike': 1}
    if query.strip():
        p['wjbt'] = query.strip()
    if version_form:
        p['bbxs'] = VERSION_FORMS[version_form]
    r = requests.get(BASE + '/fgk/' + typ, params=p, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    if d.get('code') != 0 or not isinstance(d.get('count'), int) or (not isinstance(d.get('data'), list)):
        raise ValueError('数据库返回结构异常')
    if d['count'] < 0 or len(d['data']) > page_size or ((page - 1) * page_size < d['count'] and (not d['data'])):
        raise ValueError('分类目录页数与总数不一致')
    reverse = {v: k for k, v in VERSION_FORMS.items()}
    items = []
    for x in d['data']:
        id = x.get('id', '')
        form = x.get('bbxs', '')
        if not re.fullmatch('[A-Za-z0-9]+', id) or not x.get('wjbt') or (version_form and form != VERSION_FORMS[version_form]):
            raise ValueError('文档或版本形式不符')
        items.append({'id': id, 'title': x['wjbt'], 'version_form': reverse.get(form, form), 'agency': x.get('tgjg'), 'publication_date': x.get('gbrq'), 'effective_date': x.get('sxrq'), 'detail_url': BASE + '/fgk/qrdShow?' + urlencode({'id': id, 'type': typ}), 'source_record': x})
    return {'source': '上海人大法规数据库分类查询', 'source_url': r.url, 'category': category, 'query': query.strip(), 'version_form': version_form, 'page': page, 'page_size': page_size, 'upstream_total': d['count'], 'returned': len(items), 'next_page': page + 1 if page * page_size < d['count'] and page < 100 else None, 'truncated': page * page_size < d['count'], 'items': items, 'note': '版本形式是站方标记，新制定、修改、失效、废止不等同于任何时点的效力判定；须打开详情并核对原文及后续修改。分类不是全上海所有法律文件；源更新可能改变跨页顺序。'}

def shanghai_law_category_detail(document_id, category='local', timeout=25):
    if not isinstance(document_id, str) or not re.fullmatch('[A-Za-z0-9]{1,80}', document_id):
        raise ValueError('文档 ID 无效')
    if category not in CATEGORIES:
        raise ValueError('category 须为 local、court 或 procuratorate')
    r = requests.get(BASE + '/fgk/qrdShow', params={'id': document_id, 'type': CATEGORIES[category]}, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    title = s.select_one('.detail-tit')
    a = s.select_one('.detail-right a[href*="fgkZskDownload"]')
    if title is None or a is None:
        raise ValueError('未识别详情或 PDF 链接')
    pdf = urljoin(BASE, a['href'])
    u = urlparse(pdf)
    if u.scheme != 'https' or u.netloc != 'fgk.shrd.gov.cn' or u.path != '/fileUpload/fgkZskDownload':
        raise ValueError('PDF 链接异常')
    fields = {}
    for div in s.select('.detail-left > div'):
        label = div.select_one('span')
        if label:
            fields[label.get_text(strip=True).rstrip('：:')] = div.get_text(' ', strip=True).replace(label.get_text(strip=True), '', 1).strip()
    return {'source': '上海人大法规数据库分类详情', 'source_url': r.url, 'title': title.get_text(' ', strip=True), 'fields': fields, 'pdf_url': pdf, 'note': '以站方详情显示的状态为准；法律效力及后续变化须进一步核对。'}
