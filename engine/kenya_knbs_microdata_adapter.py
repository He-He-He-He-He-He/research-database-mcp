"""肯尼亚国家统计局 KeNADA 调查和普查的元数据目录（不是统计值接口）。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode, quote
BASE = 'https://statistics.knbs.or.ke/nada/index.php/api/catalog/'
MAX_BYTES = 8000000

def _get(path):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('KNBS 目录请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    return json.loads(p.stdout)

def search(keyword, limit=10, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50) or isinstance(page, bool) or (not isinstance(page, int)) or (not 1 <= page <= 1000):
        raise ValueError('分页参数无效')
    path = 'search?' + urlencode({'sk': keyword, 'ps': limit, 'page': page})
    value = _get(path)
    result = value.get('result', {})
    if not isinstance(result.get('rows'), list):
        raise ValueError('目录返回格式异常')
    return {'source': BASE + path, 'result': result, 'note': '检索的是调查及普查元数据，不返回统计指标；数据访问权限和许可须以原站为准。'}

def metadata(idno):
    if not isinstance(idno, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,200}', idno):
        raise ValueError('无效调查 ID')
    path = quote(idno, safe='')
    data = _get(path)
    value = data.get('dataset')
    if data.get('status') != 'success' or not isinstance(value, dict) or value.get('idno') != idno:
        raise ValueError('调查元数据响应异常')
    return {'source': BASE + path, 'dataset': value, 'note': '保留原始元数据；不同字段可能存在不一致，须查原始问卷与报告。目录标签或 public 不等于已验证微观数据下载权限或条款。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=10)
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('metadata')
    q.add_argument('idno')
    a = p.parse_args()
    x = search(a.keyword, a.limit, a.page) if a.cmd == 'search' else metadata(a.idno)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
