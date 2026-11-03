"""浙大 OPAC 正常题名搜索与分页：临时会话不返回、不保存。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode
from zju_opac_api import Parser, URL
from bs4 import BeautifulSoup

def _curl(args):
    p = release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', *args], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('浙大书目服务请求失败')
    return p.stdout.decode('utf-8', 'replace')

def _parse(text):
    p = Parser()
    p.feed(text)
    m = re.search('记录\\s*(\\d+)\\s*-\\s*(\\d+)\\s*总计\\s*(\\d+)', ' '.join(p.text))
    if not m:
        raise RuntimeError('未识别结果范围：可能无结果或页面结构改变')
    return (p, tuple((int(x) for x in m.groups())))

def _single_record(html, base):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one('#content_item_list_table')
    if not table:
        return None
    text = soup.get_text(' ', strip=True)
    if not re.search('第\\s*1\\s*条记录\\s*[（(]共\\s*1\\s*条[）)]', text):
        return None
    expected = '中文文献库' if base == 'ZJU01' else '西文文献库'
    if not soup.title or expected not in soup.title.get_text(' ', strip=True):
        raise RuntimeError('单条详情页与所选中文/西文库不符')
    fields = []
    for row in table.find_all('tr'):
        label = row.select_one('td#bold')
        value = label.find_next_sibling('td') if label else None
        if label and value:
            key = ' '.join(label.get_text(' ', strip=True).split())
            val = ' '.join(value.get_text(' ', strip=True).split())
            if key and val:
                fields.append((key, val))
    ids = [v for k, v in fields if re.fullmatch('系统号-\\s*图书', k)]
    titles = [v for k, v in fields if k == '题名']
    if len(ids) != 1 or not re.fullmatch('\\d{9}', ids[0]) or len(titles) != 1:
        raise RuntimeError('单条详情缺少明确系统号或题名')
    allowed = {'题名', '著者', '责任者', '出版发行', '出版项', '载体形态', '索取号', '馆藏地:索书号'}
    description = ' ; '.join((f'{k}：{v}' for k, v in fields if k in allowed))
    return {'title': titles[0], 'description': description, 'id': base + ids[0]}

def _validate_window(window, rows, target):
    start, end, total = window
    if start != target or end < start or end > min(total, 1000) or (end - start + 1 > 10) or (len(rows) != end - start + 1):
        raise RuntimeError('页面结果范围与实际书目条数不一致')

def search(keyword, page=1, database='chinese'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词需为1–100字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码需为1–100；原站最多展示前1000条')
    if database not in ('chinese', 'western'):
        raise ValueError('数据库需为 chinese 或 western')
    base = 'ZJU01' if database == 'chinese' else 'ZJU09'
    html = _curl(['--get', '--data-urlencode', 'func=find-b', '--data-urlencode', 'find_code=WTI', '--data-urlencode', 'request=' + keyword.strip(), '--data-urlencode', 'local_base=' + base, URL])
    single = _single_record(html, base)
    if single is not None:
        if page != 1:
            raise ValueError('请求页超出可展示范围')
        return {'source': '浙江大学图书馆 OPAC', 'query': keyword.strip(), 'database': database, 'page': 1, 'total': 1, 'range_start': 1, 'range_end': 1, 'items': [single], 'note': '原站唯一命中直接显示书目详情；仅返回题录字段，不读取摘要或全文。'}
    p, window = _parse(html)
    if window[0] != 1:
        raise RuntimeError('初始检索未返回第一页')
    target = (page - 1) * 10 + 1
    if target > min(window[2], 1000):
        raise ValueError('请求页超出可展示范围')
    if page > 1:
        nav = re.search('prnnavigate\\(\\s*(\\d+),\\s*(\\d+),\\s*(\\d+),\\s*"([^"]+)"\\)', html)
        if not nav or tuple(map(int, nav.group(1, 2, 3))) != (window[2], 1, 10):
            raise RuntimeError('未确认分页控件')
        u = urlsplit(nav.group(4))
        q = parse_qs(u.query)
        if u.scheme != 'https' or u.hostname != 'opac.zju.edu.cn' or u.username or u.password or (u.port not in (None, 443)) or (not re.fullmatch('/F/[A-Z0-9-]+', u.path)) or (q != {'func': ['short-jump'], 'jump': ['1']}):
            raise RuntimeError('分页地址格式不符合安全约束')
        q['jump'] = [str(target)]
        url = urlunsplit((u.scheme, u.netloc, u.path, urlencode(q, doseq=True), ''))
        p, window = _parse(_curl([url]))
        if window[0] != target:
            raise RuntimeError('分页结果起点不符')
    _validate_window(window, p.rows, target)
    if any((not isinstance(row.get('id'), str) or not re.fullmatch(re.escape(base) + '\\d{9}', row['id']) for row in p.rows)):
        raise RuntimeError('书目编号与所选中文/西文库不符')
    return {'source': '浙江大学图书馆 OPAC', 'query': keyword.strip(), 'database': database, 'page': page, 'total': window[2], 'range_start': window[0], 'range_end': window[1], 'items': p.rows, 'note': '仅题名关键词搜索；按原站结果顺序，网站最多展示前1000条。未读取全文，不保留临时会话地址。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--database', choices=['chinese', 'western'], default='chinese')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.database), ensure_ascii=False, indent=2))
