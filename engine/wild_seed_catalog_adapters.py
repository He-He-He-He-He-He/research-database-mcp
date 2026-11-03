"""国家重要野生植物种质资源库公开检索，返回资源目录信息。"""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://seed.iflora.cn'
FIELDS = ('rs_id', '种中文名', '拉丁简名', 'rs_type', '科拉丁名', '采集编号', 'rs_organization', '采集时间', '省自治区', 'rs_share', '形态数据内容', '萌发率')

def search(keyword='', page=1, limit=10, resource_type='', province=''):
    if not 1 <= int(page) <= 10000 or int(limit) not in (10, 20):
        raise ValueError('页码须为正整数，每页条数为 10 或 20')
    params = {'q': keyword, 'page': int(page), 'limit': int(limit), 'kldm': '', 'zldm': '', 'zzwm': '', 'szzq': province, 'rstype': resource_type, 'rsorganization': '', 'rsshare': '', 'orderby': '', 'descasc': ''}
    url = BASE + '/Home/SearchList?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('资源库请求失败: ' + p.stderr.strip())
    try:
        data = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError('资源库响应不是 JSON，可能站点报错或接口已改变') from exc
    if str(data.get('code')) != '0' or not isinstance(data.get('data'), list) or (not str(data.get('count', '')).isdigit()):
        raise RuntimeError('资源库返回错误或未知结构: ' + str(data.get('msg', '')))
    items = []
    for entry in data['data']:
        item = {k: entry.get(k) for k in FIELDS if k in entry}
        if entry.get('rs_id') is not None:
            item['detail_url'] = BASE + '/Home/Detail?' + urlencode({'id': entry['rs_id']})
        items.append(item)
    return {'source': '国家重要野生植物种质资源库', 'keyword': keyword, 'page': int(page), 'limit': int(limit), 'total': int(data['count']), 'items': items}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keyword', nargs='?', default='')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--limit', type=int, choices=(10, 20), default=10)
    parser.add_argument('--type', default='', dest='resource_type')
    parser.add_argument('--province', default='')
    args = parser.parse_args()
    print(json.dumps(search(args.keyword, args.page, args.limit, args.resource_type, args.province), ensure_ascii=False, indent=2))
