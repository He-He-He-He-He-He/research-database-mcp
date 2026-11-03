"""二十五史研习系统：文献和知识库搜索分组。"""
import release_runtime
import re
from urllib.parse import quote, urljoin, urlsplit, unquote
import requests
from bs4 import BeautifulSoup
BASE = 'http://www.chinabooktrading.com:81/h25/'

def search(keyword, limit=20):
    if not isinstance(keyword, str) or not re.fullmatch('[\\u3400-\\u9fff]{1,40}', keyword):
        raise ValueError('目前只支持 1–40 个连续汉字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200):
        raise ValueError('返回分组数量须为 1–200')
    r = requests.get(BASE + 'QUERY/' + quote(keyword), timeout=30)
    r.raise_for_status()
    h = BeautifulSoup(r.content, 'html.parser')
    if not h.title or h.title.get_text(' ', strip=True) != '檢索：' + keyword:
        raise RuntimeError('查询页标题与关键词不符')
    out = []
    for a in h.select('a[href]'):
        text = a.get_text(' ', strip=True)
        if '中共檢索到' not in text:
            continue
        m = re.fullmatch('在\\s*(/.*?)\\s*中共檢索到\\s*(\\d+)\\s*條結果', text)
        if not m:
            raise RuntimeError('原站分组记录格式变化')
        u = urljoin(BASE, a['href'])
        p = urlsplit(u)
        if p.scheme != 'http' or p.hostname != 'www.chinabooktrading.com' or p.port != 81 or (not unquote(p.path).startswith('/h25/QUERY/' + keyword + '/')):
            raise RuntimeError('原站分组链接异常')
        out.append({'group_path_raw': m.group(1), 'matches': int(m.group(2)), 'url': u})
    return {'source': '二十五史研习系统分组检索', 'query': keyword, 'group_count': len(out), 'groups': out[:limit], 'note': '实际结果包含正史、其他文献与知识库；分组命中次数不是去重后的文献数量。上游 HTTP 明文，请勿输入敏感词；学校身份、正文及权限未核验。无分组仅描述本次响应。'}
