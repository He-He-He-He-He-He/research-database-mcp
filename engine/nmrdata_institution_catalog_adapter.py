"""Campus-IP NMRData compound-name literature catalog, without spectra."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.nmrdata.com/'
TURN = 'https://libdb.zju.edu.cn/s/lib/libtb/turning/1373'

def _identity(p):
    return bool(re.search('当前单位\\s*[：:]\\s*浙江大学', p.get_text(' ', strip=True)))

def _clean(v):
    return ' '.join(v.split())

def search(keyword, page=1, limit=10, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(TURN, timeout=20)
    r.raise_for_status()
    r = s.get(BASE + 'ChemicalSearch.aspx', timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if not _identity(p):
        raise RuntimeError('未确认浙江大学机构身份')
    form = {x['name']: x.get('value', '') for x in p.select('input[type=hidden][name]')}
    btn = p.select_one('#btnSearch')
    if not {'__VIEWSTATE', '__EVENTVALIDATION'}.issubset(form) or not btn:
        raise RuntimeError('检索表单状态缺失')
    form.update({'txtContent': q, 'btnSearch': btn.get('value', '')})
    r = s.post(BASE + 'ChemicalSearch.aspx', data=form, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if page > 1:
        r = s.get(BASE + 'ChemicalDetail.aspx', params={'Page': page}, timeout=25)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
    if not _identity(p):
        raise RuntimeError('结果页机构身份未确认')
    label = p.select_one('#lblCount')
    m = re.search('搜索\\s*(.*?)\\s*获得约\\s*([\\d,]+)\\s*条结果', label.get_text(' ', strip=True) if label else '')
    pg = re.search('当前页\\s*[：:]\\s*(\\d+)\\s*/\\s*(\\d+)', p.get_text(' ', strip=True))
    if not m or m.group(1).strip() != q or (not pg) or (int(pg.group(1)) != page):
        raise RuntimeError('结果关键词或页码不符')
    total = int(m.group(2).replace(',', ''))
    items = []
    for row in p.select('#dtlDisplay blockquote'):
        cols = row.select('p')
        if len(cols) < 4:
            raise RuntimeError('题录字段缺失')
        item = {'compound': _clean(cols[0].get_text(' ', strip=True)), 'source': _clean(cols[1].get_text(' ', strip=True)), 'title': _clean(cols[2].get_text(' ', strip=True)), 'authors': _clean(cols[3].get_text(' ', strip=True))}
        link = row.find('a', href=re.compile('^javascript:cdd\\('))
        m_id = re.fullmatch("javascript:cdd\\('([0-9a-fA-F-]{36})'\\)", link.get('href', '')) if link else None
        item['record_id'] = m_id.group(1) if m_id else None
        items.append(item)
    if len(items) > 10 or (total and (not items) and (page <= int(pg.group(2)))):
        raise RuntimeError('检索题录异常')
    return {'source': '微谱数据化合物文献', 'institution': '浙江大学', 'query': q, 'page': page, 'total_approximate': total, 'total_pages': int(pg.group(2)), 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '化合物名称文献检索，结果数为页面标注约数；仅题录，不读取结构和核磁谱图。limit 仅截取原站当前页，若 truncated 为 true，继续请求下一站方页会遗漏本页未返回记录，请用 limit=10 取整页。'}
