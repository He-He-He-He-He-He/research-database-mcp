"""文化和旅游部数据服务栏目世界文化遗产公开页面列表。"""
import release_runtime
import json, subprocess
from bs4 import BeautifulSoup
URL = 'https://sjfw.mct.gov.cn/site/dataservice/culture'

def search(keyword='', region='', year=''):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', URL], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('文旅部数据服务读取失败（curl %s）' % p.returncode)
    soup = BeautifulSoup(p.stdout, 'html.parser')
    root = soup.select_one('#province .list')
    if root is None:
        raise RuntimeError('未找到遗产列表')
    lines = []
    total_records = 0
    header_seen = False
    for li in root.select(':scope > .li'):
        cells = [x.get_text(' ', strip=True) for x in li.select(':scope > .span')]
        if len(cells) != 3:
            raise RuntimeError('遗产条目字段不符合预期')
        if cells == ['名称', '地点', '登录年份']:
            header_seen = True
            continue
        if not all(cells):
            raise RuntimeError('遗产条目存在缺失字段')
        total_records += 1
        if keyword in cells[0] and region in cells[1] and (year in cells[2]):
            lines.append({'name': cells[0], 'location': cells[1], 'inscription_year_text': cells[2]})
    if not header_seen or not total_records:
        raise RuntimeError('未能识别非空遗产列表，网页结构可能变化')
    displayed = soup.select_one('.culture1 .time')
    return {'source': '文化和旅游部数据服务栏目—世界文化遗产', 'url': URL, 'displayed_cutoff': displayed.get_text(' ', strip=True) if displayed else None, 'count': len(lines), 'items': lines, 'note': '提取服务器返回的世界文化遗产页面条目；页面显示数据截止日期为2024年，但列表含2025年条目且部分说明仍述2021年，更新时间标识不一致，不能当成权威完整现状或包含所有自然遗产；年份与地点按原样保留。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--region', default='')
    p.add_argument('--year', default='')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.region, a.year), ensure_ascii=False, indent=2))
