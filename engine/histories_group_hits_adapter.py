"""二十五史研习系统单个来源分组的章节命中。"""
import release_runtime
import re
from urllib.parse import urlsplit, unquote, urljoin
import requests
from bs4 import BeautifulSoup
from histories_public_groups_adapter import search as groups_search, BASE

def search(keyword, group, page=1, limit=50):
    if not isinstance(group, str) or not group.startswith('/') or (not group.endswith('/')) or (len(group) > 200):
        raise ValueError('请提供分组查询返回的完整来源路径')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码须为 1–100')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('返回条数须为 1–50')
    result = groups_search(keyword, 200)
    matches = [g for g in result['groups'] if g['group_path_raw'] == group]
    if len(matches) != 1:
        raise ValueError('当前前 200 个分组中未找到该来源路径')
    g = matches[0]
    url = g['url']
    if not url.endswith('/page/1'):
        raise RuntimeError('来源链接格式异常')
    url = url[:-1] + str(page)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    h = BeautifulSoup(r.content, 'html.parser')
    if not h.title or h.title.get_text(' ', strip=True) != f'在 {group} 中檢索：{keyword}':
        raise RuntimeError('原站未确认来源及关键词')
    items = []
    prefix = '/h25/QUERY/' + keyword + group + 'page/' + str(page) + '/'
    for a in h.select('a[href]'):
        title = a.get_text(' ', strip=True)
        u = urljoin(BASE, a['href'])
        p = urlsplit(u)
        if not title or not unquote(p.path).startswith(prefix):
            continue
        if p.scheme != 'http' or p.hostname != 'www.chinabooktrading.com' or p.port != 81:
            raise RuntimeError('异常结果来源')
        if not re.fullmatch('(?:[0-9a-f]{64}|[0-9a-f]{80})', unquote(p.path)[len(prefix):]):
            raise RuntimeError('原站命中编号异常')
        items.append({'title': title, 'url': u})
    return {'source': '二十五史研习系统分组章节命中', 'query': keyword, 'group': group, 'group_matches_raw': g['matches'], 'page_requested': page, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '站方结果以章节或片段为单位，命中次数非去重书数；页面未独立回显页码，结果链接所含页码已核对。HTTP 明文，勿输入敏感词；学校身份及正文权限未核验。空页含义不确定；limit只截取当前源页，若truncated为true，翻下一页会漏当前页其余条目，请用limit=50读取本站页。'}
