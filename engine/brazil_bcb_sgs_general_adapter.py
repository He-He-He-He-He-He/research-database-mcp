"""巴西央行公开数据目录和 SGS 时间序列 API。"""
import release_runtime
import argparse
from datetime import date
import json
import re
import subprocess
from urllib.parse import urlencode
CAT = 'https://dadosabertos.bcb.gov.br/api/3/action/'
DATA = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.'
MAX_BYTES = 10000000

def _get(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('巴西央行请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return json.loads(p.stdout)

def search(keyword, limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 10000):
        raise ValueError('无效分页')
    url = CAT + 'package_search?' + urlencode({'q': keyword, 'rows': limit, 'start': offset})
    data = _get(url)
    if not data.get('success') or not isinstance(data.get('result', {}).get('results'), list):
        raise ValueError('目录响应异常')
    return {'source': url, 'result': data['result'], 'note': '央行开放数据目录含 SGS 之外的数据集；先核查名称、来源、频率和资源链接。'}

def metadata(slug):
    if not isinstance(slug, str) or not re.fullmatch('[a-z0-9][a-z0-9_-]{0,180}', slug):
        raise ValueError('无效目录名称')
    url = CAT + 'package_search?' + urlencode({'q': '*:*', 'fq': 'name:"' + slug + '"', 'rows': 2})
    data = _get(url)
    result = data.get('result', {}).get('results', [])
    if not data.get('success') or len(result) != 1 or result[0].get('name') != slug:
        raise ValueError('未找到唯一目录元数据')
    return {'source': url, 'metadata': result[0], 'note': '由目录精确名称检索元数据；单位、定义和可用范围须由相应原始条目确认。'}

def observations(series, start, end):
    if isinstance(series, bool) or not re.fullmatch('[0-9]{1,10}', str(series)):
        raise ValueError('序列代码须为数字')
    try:
        first = date.fromisoformat(start)
        last = date.fromisoformat(end)
    except (TypeError, ValueError):
        raise ValueError('日期须为 YYYY-MM-DD')
    if first > last or (last - first).days > 3652:
        raise ValueError('日期顺序错误或跨度超过十年')
    url = DATA + str(series) + '/dados?' + urlencode({'formato': 'json', 'dataInicial': first.strftime('%d/%m/%Y'), 'dataFinal': last.strftime('%d/%m/%Y')})
    value = _get(url)
    if not isinstance(value, list) or any((not isinstance(x, dict) or 'data' not in x or 'valor' not in x for x in value)):
        raise ValueError('SGS 结果格式异常')
    return {'source': url, 'series': str(series), 'start': start, 'end': end, 'observations': value, 'count': len(value), 'note': '原样保留葡语日期及值字符串；数据端不附定义、单位或频率，使用前须核对官方目录元数据。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--offset', type=int, default=0)
    q = s.add_parser('metadata')
    q.add_argument('slug')
    q = s.add_parser('data')
    q.add_argument('series')
    q.add_argument('start')
    q.add_argument('end')
    a = p.parse_args()
    value = search(a.keyword, a.limit, a.offset) if a.cmd == 'search' else metadata(a.slug) if a.cmd == 'metadata' else observations(a.series, a.start, a.end)
    print(json.dumps(value, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
