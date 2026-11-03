"""国家新闻出版署电子期刊、图书音像电子出版单位及发行企业查询。"""
import release_runtime
import argparse
import json
import subprocess
TYPES = {'serial': ('291531', 'https://www.nppa.gov.cn/bsfw/cyjghcpcx/lxdz/'), 'books': ('232854', 'https://www.nppa.gov.cn/bsfw/cyjghcpcx/tcdw/'), 'electronic': ('232854', 'https://www.nppa.gov.cn/bsfw/cyjghcpcx/dzcb/'), 'audiovisual': ('232854', 'https://www.nppa.gov.cn/bsfw/cyjghcpcx/yxcb/'), 'distribution': ('234320', 'https://www.nppa.gov.cn/bsfw/cyjghcpcx/fxjg/')}

def search(kind, page=1, name='', region='', number=''):
    if kind not in TYPES:
        raise ValueError('类别须为 serial、books、electronic、audiovisual、distribution')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if any((not isinstance(x, str) or len(x) > 100 for x in (name, region, number))):
        raise ValueError('检索参数无效')
    if kind == 'serial':
        if region:
            raise ValueError('连续型电子出版物无地区筛选参数')
        form = {'qkkh': number, 'qkmc': name, 'cbdw': '', 'zgdw': '', 'zbdw': '', 'beiz': ''}
    elif kind in ('books', 'electronic', 'audiovisual'):
        if number:
            raise ValueError('出版单位无刊号筛选参数')
        form = {'dwmc': name, 'diqu': region, 'zgdw': '', 'zbdw': '', 'leix': {'books': '33', 'electronic': '37', 'audiovisual': '36'}[kind]}
    else:
        if region or number:
            raise ValueError('发行企业在此接口只支持名称筛选')
        form = {'dwmc': name, 'leix': ''}
    cid, source = TYPES[kind]
    form = {'page': str(page), 'size': '20', **form}
    cmd = ['curl', '--fail', '--silent', '--show-error', '--max-time', '20', 'https://www.nppa.gov.cn/was5/web/search?channelid=' + cid]
    for k, v in form.items():
        cmd.extend(['--data-urlencode', k + '=' + v])
    obj = json.loads(release_runtime.run(cmd, check=True, capture_output=True).stdout.decode('utf-8-sig'))
    if not isinstance(obj.get('total'), int) or (obj.get('data') is not None and (not isinstance(obj['data'], list))):
        raise ValueError('上游结构变化')
    return {'kind': kind, 'source': source, 'filters': {'name': name, 'region': region, 'number': number}, 'page': page, 'page_size': 20, 'total': obj['total'], 'items': obj.get('data') or [], 'note': '保留原字段；记录和数量随官网变化，不能据此推断当前有效或年度核验状态。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=TYPES)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--name', default='')
    p.add_argument('--region', default='')
    p.add_argument('--number', default='')
    a = p.parse_args()
    print(json.dumps(search(a.kind, a.page, a.name, a.region, a.number), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
