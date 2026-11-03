"""Third national industrial census: 1995 major product output table."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/tjgb/gypcgb/qggypcgb/202302/t20230218_1913196.html'

def products(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    with requests.get(URL, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    blocks = []
    for p in soup.select('p'):
        if p.find('p') or not ''.join(p.get_text().split()).startswith('表1：主要产品产量及增长情况'):
            continue
        sibling = p.find_next_sibling('p')
        if sibling:
            blocks.append(sibling.get_text('\n', strip=True))
    blocks = list(dict.fromkeys(blocks))
    if len(blocks) != 1:
        raise ValueError('expected one unique product table')
    lines = [' '.join(line.split()) for line in blocks[0].splitlines() if line.strip()]
    if not lines or '1995年产量' not in lines[0] or '比1985年增长' not in lines[0]:
        raise ValueError('unexpected source header')
    rows = []
    for line in lines[1:]:
        m = re.fullmatch('(.+?)\\s+([0-9.]+)\\s*(\\S+)\\s+([0-9.]+)\\s*(%|倍)', line)
        if not m:
            raise ValueError('unexpected row: ' + line)
        rows.append({'product': m.group(1), 'output': m.group(2), 'output_unit': m.group(3), 'growth_vs_1985': m.group(4), 'growth_unit': m.group(5), 'source_row': line})
    if len(rows) != 21 or len({r['product'] for r in rows}) != 21:
        raise ValueError('expected 21 unique product rows')
    items = [r for r in rows if keyword in r['product']]
    return {'source': '国家统计局第三次全国工业普查主要数据公报', 'source_url': URL, 'year': 1995, 'table': '表1：主要产品产量及增长情况', 'total': len(rows), 'matched_count': len(items), 'items': items, 'note': 'total 为原表全部产品行数，matched_count 为产品名称关键词命中数；产量为1995年，增长以1985年为基期；原文区分百分比和增长倍数，不自动转换成倍数或同比；产品定义及普查覆盖范围须核公报。'}
