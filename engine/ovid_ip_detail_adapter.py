"""在浙大 Ovid 临时会话中搜索并读取 MEDLINE / LWW 等题录。"""
import release_runtime
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from ovid_cab_adapter import ENTRY, _ovid_url, _request
from ovid_ip_resources_adapter import RESOURCES
FIELDS = {'Unique Identifier:': 'unique_identifier', 'Authors:': 'authors_raw', 'Authors Full Name:': 'authors_full_raw', 'PMC Identifier:': 'pmc_identifier', 'Accession Number:': 'accession_number', 'Author:': 'authors_raw', 'Title:': 'title', 'Source:': 'source_raw', 'Page Count:': 'page_count_raw', 'Publisher:': 'publisher', 'Country of Publication:': 'country_raw', 'Digital Object Identifier:': 'doi_raw', 'Subject Headings:': 'subject_headings_raw', 'Organism Descriptors:': 'organism_descriptors_raw', 'Geographic Location:': 'geographic_location_raw', 'Language:': 'language_raw', 'Publication Type:': 'publication_type_raw', 'Year of Publication:': 'year_raw', 'Abstract:': 'abstract_raw'}

def _parse_detail(page, expected_title, include_abstract):
    out = {}
    for tr in page.select('tr'):
        th = tr.find('th', recursive=False)
        td = tr.find('td', recursive=False)
        if not th or not td:
            continue
        name = FIELDS.get(th.get_text(' ', strip=True))
        if not name or (name == 'abstract_raw' and (not include_abstract)):
            continue
        value = td.get_text(' ', strip=True)
        if name in out:
            raise RuntimeError('Ovid 详情有重复字段，无法可靠解析')
        out[name] = value

    def norm(s):
        return ' '.join(s.split())
    if not out.get('title') or norm(out['title']) != norm(expected_title):
        raise RuntimeError('Ovid 详情题名与所选结果不一致')
    if not out.get('unique_identifier') and (not out.get('accession_number')):
        raise RuntimeError('Ovid 详情缺少记录编号')
    return out

def detail(query, resource='medline', start=1, include_abstract=False):
    if resource != 'medline':
        raise ValueError('当前仅支持 Ovid MEDLINE；其他资源详情结构尚未适配')
    db, expected_resource, scope = RESOURCES[resource]
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('检索词须为 1–200 字单行文本')
    if type(start) is not int or not 1 <= start <= 1000000 or type(include_abstract) is not bool:
        raise ValueError('记录序号或摘要参数无效')
    s = requests.Session()
    r = _request(s, 'get', ENTRY, timeout=25)
    u = urlparse(r.url)
    if u.scheme != 'https' or u.hostname not in ('ovidsp.dc1.ovid.com', 'ovidsp.dc2.ovid.com'):
        raise RuntimeError('馆藏入口未进入预期 Ovid 服务')
    p = BeautifulSoup(r.content, 'html.parser')
    link = next((a for a in p.select('a.resource-dblink[href]') if a.get('db_full_name') == db), None)
    if not link:
        raise RuntimeError('Ovid 未提供所选资源')
    r = _request(s, 'get', _ovid_url(r.url, link['href']), timeout=25)
    p = BeautifulSoup(r.content, 'html.parser')
    f = p.select_one('form#sfeasy')
    if not f or not f.get('action'):
        raise RuntimeError('Ovid 未显示预期搜索表单')
    data = {i['name']: i.get('value', '') for i in f.select('input[type=hidden][name]')}
    data.update({'textBox': query.strip(), 'submit:Perform Search|1': '搜索'})
    r = _request(s, 'post', _ovid_url(r.url, f['action']), data=data, timeout=45)
    p = BeautifulSoup(r.content, 'html.parser')
    info = p.select_one('#searchaid-numbers')
    resource = p.select_one('#ovid-resources-link-block')
    match = re.search('([\\d,]+)\\s*个文本结果', info.get_text(' ', strip=True)) if info else None
    if not match or not resource or expected_resource not in resource.get_text(' ', strip=True):
        raise RuntimeError('Ovid 未确认所选资源和结果数')
    total = int(match.group(1).replace(',', ''))
    if start > total:
        raise ValueError('选定序号超出本次结果范围')
    if start > 1:
        nav = p.select_one('form#nav-results')
        button = nav.select_one('#toolbar-go-option input[type=submit][name]') if nav else None
        if not nav or not nav.get('action') or (not button):
            raise RuntimeError('Ovid 未显示结果跳转表单')
        data = {i['name']: i.get('value', '') for i in nav.select('input[type=hidden][name]')}
        data.update({'startRecord': str(start), button['name']: button.get('value', '')})
        r = _request(s, 'post', _ovid_url(r.url, nav['action']), data=data, timeout=45)
        p = BeautifulSoup(r.content, 'html.parser')
    pos = p.select_one('#startRecord')
    exp = p.select_one('#searchaid-explain')
    row = p.select_one('td.titles-record')
    if not pos or pos.get('value') != str(start) or (not exp) or (query.strip() not in exp.get_text(' ', strip=True)) or (not row):
        raise RuntimeError('Ovid 未确认搜索词或记录位置')
    tr = row.find_parent('tr')
    num = re.match('^\\s*(\\d+)\\.', tr.get_text(' ', strip=True) if tr else '')
    link = row.select_one('a.citation_title[href]')
    if not num or int(num.group(1)) != start or (not link):
        raise RuntimeError('Ovid 未确认所选题录')
    expected = link.get_text(' ', strip=True)
    r = _request(s, 'get', _ovid_url(r.url, link['href']), timeout=25)
    p = BeautifulSoup(r.content, 'html.parser')
    fields = _parse_detail(p, expected, include_abstract)
    return {'source': 'Ovid 机构会话 / ' + db, 'library_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1005', 'resource': db, 'scope': scope, 'query': query.strip(), 'result_position': start, 'total': total, 'fields': fields, 'note': '每次新建学校机构会话并重新检索；记录排序可能变化，序号仅属于本次结果，详情题名已核对。题录不代表全文许可；不返回会话链接或作者邮箱。' + ('摘要原样来自上游题录；' if include_abstract else '')}
