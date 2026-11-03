"""ClinicalTrials.gov API v2 public study search and details."""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
ROOT = 'https://clinicaltrials.gov/api/v2/studies'

def _get(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError(f'ClinicalTrials.gov 请求失败 (curl 状态 {p.returncode})')
    data = json.loads(p.stdout)
    if not isinstance(data, dict):
        raise ValueError('上游响应格式异常')
    return data

def search(condition, size=10, page_token=None):
    if not condition or not condition.strip():
        raise ValueError('疾病或关键词不能为空')
    if not 1 <= size <= 100:
        raise ValueError('每页条数应为 1–100')
    params = {'query.cond': condition, 'pageSize': size, 'countTotal': 'true', 'format': 'json'}
    if page_token:
        params['pageToken'] = page_token
    data = _get(ROOT + '?' + urlencode(params))
    if not isinstance(data.get('studies'), list):
        raise ValueError('未识别试验列表')
    return data

def detail(nct_id):
    if not re.fullmatch('NCT\\d{8}', nct_id):
        raise ValueError('试验编号应为 NCT 加 8 位数字')
    data = _get(ROOT + '/' + nct_id + '?format=json')
    if data.get('protocolSection', {}).get('identificationModule', {}).get('nctId') != nct_id:
        raise ValueError('返回的试验编号不一致')
    return data

def main():
    p = argparse.ArgumentParser(description='ClinicalTrials.gov 公开试验信息')
    sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('search')
    s.add_argument('condition')
    s.add_argument('--size', type=int, default=10)
    s.add_argument('--page-token')
    d = sp.add_parser('detail')
    d.add_argument('nct_id')
    a = p.parse_args()
    try:
        print(json.dumps(search(a.condition, a.size, a.page_token) if a.cmd == 'search' else detail(a.nct_id), ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
