"""浙江省行政规范性文件库的只读文件目录检索。"""
import release_runtime
import json
import subprocess
ENDPOINT = 'https://zjsftbascweb.zjsft.gov.cn/data/zjdatabase/census/fLibrary/getDocPage'

def regions():
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', 'https://zjsftbascweb.zjsft.gov.cn/data/zjdatabase/census/fLibrary/getArea'], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('地区目录请求失败: ' + p.stderr.strip())
    try:
        result = json.loads(p.stdout)['result']
        if result['code'] != 4000 or not isinstance(result['data'], list):
            raise ValueError('无效目录')
        return result['data']
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('地区目录响应格式已变化') from exc

def search(keyword='', page=1, page_size=15, agency='', document_number='', area='ZJS', department_class='10'):
    if not 1 <= int(page) <= 10000 or not 1 <= int(page_size) <= 100:
        raise ValueError('页码须为正整数，每页数量须为 1–100')
    payload = {'area': area, 'deptClass': department_class, 'docTitle': keyword, 'page': {'pageNum': int(page), 'pageSize': int(page_size)}}
    if agency:
        payload['formulateAgencyName'] = agency
    if document_number:
        payload['fileNo'] = document_number
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '-H', 'Content-Type: application/json', '--data-binary', json.dumps(payload, ensure_ascii=False), ENDPOINT], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('浙江文件库请求失败: ' + p.stderr.strip())
    try:
        response = json.loads(p.stdout)
        result = response['result']
        if result['code'] != 4000:
            raise RuntimeError('浙江文件库返回错误: ' + str(result.get('message', '')))
        data = result['data']
        if not isinstance(data['rows'], list):
            raise ValueError('rows 不是列表')
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('浙江文件库响应格式已变化或不是 JSON') from exc
    return {'source': '浙江省行政规范性文件库', 'keyword': keyword, 'area': area, 'department_class': department_class, 'page': int(page), 'page_size': int(page_size), 'total': data['total'], 'pages': data['pages'], 'items': data['rows']}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keyword', nargs='?', default='')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--page-size', type=int, default=15)
    parser.add_argument('--agency', default='')
    parser.add_argument('--number', default='')
    parser.add_argument('--area', default='ZJS', help='地区编码，参见 --regions')
    parser.add_argument('--department-class', default='10', help='机关分类编码')
    parser.add_argument('--regions', action='store_true', help='列出网站公开地区和机关分类')
    args = parser.parse_args()
    print(json.dumps(regions() if args.regions else search(args.keyword, args.page, args.page_size, args.agency, args.number, args.area, args.department_class), ensure_ascii=False, indent=2))
