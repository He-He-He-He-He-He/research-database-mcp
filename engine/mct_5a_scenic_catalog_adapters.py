"""文旅部数据服务网页 5A 级景区目录，只读。"""
import release_runtime
import json, re, subprocess
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
ROOT = 'https://sjfw.mct.gov.cn'
URL = ROOT + '/site/dataservice/base'

def fetch(url):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('文旅部数据服务请求失败（curl %s）' % r.returncode)
    return r.stdout.decode('utf8')

def objects(text):
    starts = list(re.finditer('\\{id:(?:\\d+(?:e\\d+)?),grade:', text))
    result = []
    for marker in starts:
        i = marker.start()
        j = i
        depth = 0
        quoted = False
        escaped = False
        while j < len(text):
            ch = text[j]
            if quoted:
                if escaped:
                    escaped = False
                elif ch == '\\':
                    escaped = True
                elif ch == '"':
                    quoted = False
            elif ch == '"':
                quoted = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            raise RuntimeError('景区数据对象不完整')
        result.append(text[i:j + 1])
    return result

def field(obj, name):
    match = re.search('(?:^|[,\\{])' + re.escape(name) + ':("(?:\\\\.|[^"\\\\])*")', obj)
    if not match:
        raise RuntimeError('景区字段 %s 缺失或结构变化' % name)
    return json.loads(match.group(1))

def search(keyword='', region='', year='', page=1, page_size=20):
    if not 1 <= int(page) <= 10000 or not 1 <= int(page_size) <= 100:
        raise ValueError('页码须为正整数且每页不超过 100 条')
    html = fetch(URL)
    soup = BeautifulSoup(html, 'html.parser')
    found = []
    for x in soup.find_all('script', src=True):
        u = urljoin(URL, x['src'])
        p = urlsplit(u)
        if p.scheme == 'https' and p.netloc == 'sjfw.mct.gov.cn' and re.fullmatch('/_nuxt/[0-9a-f]+\\.js', p.path):
            script = fetch(u)
            if 'var data=[{province:' in script:
                found.append((u, script))
    if len(found) != 1:
        raise RuntimeError('未唯一识别景区数据源')
    asset, script = found[0]
    records = []
    for obj in objects(script):
        m = re.match('\\{id:(\\d+(?:e\\d+)?),', obj)
        try:
            identifier = str(int(Decimal(m.group(1))))
        except (AttributeError, InvalidOperation):
            raise RuntimeError('景区 ID 格式变化')
        records.append({'id': identifier, 'name': field(obj, 'name'), 'description': field(obj, 'desc'), 'region': field(obj, 'place'), 'year_text': field(obj, 'year'), 'published_text': field(obj, 'created_at')})
    if not records or len({x['id'] for x in records}) != len(records):
        raise RuntimeError('景区列表为空或 ID 重复')
    selected = [x for x in records if keyword in x['name'] and region in x['region'] and (year in x['year_text'])]
    start = (int(page) - 1) * int(page_size)
    return {'source': '文化和旅游部数据服务栏目 5A 级景区', 'url': URL, 'asset_url': asset, 'snapshot_count': len(records), 'total': len(selected), 'page': int(page), 'page_size': int(page_size), 'items': selected[start:start + int(page_size)], 'note': '读取网页公开前端内嵌数据并本地筛选，不执行站点脚本。页面数据可能滞后且年份字段与文字描述可能冲突，景区当前评级、开放及营业信息需核验最新官方公告。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--region', default='')
    p.add_argument('--year', default='')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.region, a.year, a.page, a.page_size), ensure_ascii=False, indent=2))
