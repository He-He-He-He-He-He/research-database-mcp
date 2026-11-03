"""国家新闻出版署网络出版服务单位许可证公开查询。"""
import release_runtime
import argparse
import json
import subprocess
URL = 'https://www.nppa.gov.cn/was5/web/search?channelid=205336'
PAGE = 'https://www.nppa.gov.cn/bsfw/cyjghcpcx/wlcb/'

def search(name='', region='', page=1):
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('page须为正整数')
    if not isinstance(name, str) or not isinstance(region, str) or len(name) > 100 or (len(region) > 40):
        raise ValueError('名称或地区格式不符')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', URL]
    for key, val in [('page', str(page)), ('size', '20'), ('dwmc', name), ('diqu', region)]:
        args += ['--data-urlencode', key + '=' + val]
    output = release_runtime.run(args, check=True, capture_output=True).stdout.decode('utf-8-sig')
    result = json.loads(output)
    if not isinstance(result, dict) or not isinstance(result.get('total'), int) or (result.get('data') is not None and (not isinstance(result['data'], list))):
        raise ValueError('上游结果格式变化')
    return {'source': PAGE, 'name': name, 'region': region, 'page': page, 'page_size': 20, 'total': result['total'], 'items': result.get('data') or [], 'note': '以官网原始名称、地区、有效期为准；目录出现不代表许可当前有效或范围未发生变化。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--name', default='')
    p.add_argument('--region', default='')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.name, a.region, a.page), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
