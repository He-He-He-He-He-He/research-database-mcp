"""历代进士登科馆藏姓名检索，单次查询，返回上游 JSON。"""
import release_runtime
import argparse, json, subprocess, sys
ENDPOINT = 'https://examination.ancientbooks.cn/docDengke/dkSearchTable.jspx'

def search_jinshi(name, page=1):
    if not isinstance(name, str) or not name.strip() or len(name) > 100 or ('\n' in name) or ('\r' in name):
        raise ValueError('姓名需为1–100字单行文本')
    if not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    params = {'bookType': '0', 'searchType': '1', 'title': name.strip(), 'type': 'fullName', 'pageNo': str(page), 'pageSize': '15'}
    cmd = ['/usr/bin/curl', '--silent', '--show-error', '--fail', '--max-time', '20', '--get']
    for key, value in params.items():
        cmd.extend(['--data-urlencode', key + '=' + value])
    cmd.append(ENDPOINT)
    try:
        r = release_runtime.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('检索请求失败，请检查网络或机构权限') from e
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError('网站未返回JSON，请检查认证或网站状态') from e
    if data.get('code') != 0 or not isinstance(data.get('data'), list):
        raise RuntimeError('上游返回错误或数据结构变化')
    return {'query': name.strip(), 'source': '历代进士登科数据库姓名检索', 'page': page, 'count': data.get('count'), 'totalPage': data.get('totalPage'), 'items': data['data']}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='历代进士登科数据库姓名检索')
    p.add_argument('name')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    try:
        print(json.dumps(search_jinshi(a.name, a.page), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
