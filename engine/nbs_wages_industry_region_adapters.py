"""国家统计局分地区、行业及岗位的城镇单位就业人员平均工资。"""
import release_runtime
import json, subprocess
from moe_education_statistics_adapters import _LeafTables
URLS = {2023: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202405/t20240520_1950434.html', 2024: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202505/t20250516_1959826.html', 2025: 'https://www.stats.gov.cn/sj/zxfb/202605/t20260515_1963707.html'}
TITLES = ['城镇非私营单位分区域', '城镇非私营单位分行业', '城镇非私营单位分登记注册类别', '城镇私营单位分区域', '城镇私营单位分行业', '规模以上企业分区域及岗位', '规模以上企业分行业及岗位', '规模以上企业分登记注册类别及岗位']

def report(year, table=0, keyword=''):
    if any((isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, str) and v.isascii() and v.isdigit())) for v in (year, table))):
        raise ValueError('年份和表号须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if int(year) not in URLS:
        raise ValueError('仅支持 2023—2025 年')
    if int(table) not in range(9):
        raise ValueError('表号为 0（全部）或 1—8')
    url = URLS[int(year)]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('国家统计局工资报告读取失败（curl %s）' % p.returncode)
    html = p.stdout.decode('utf-8')
    if f'{year}年城镇单位就业人员年平均工资情况' not in html:
        raise RuntimeError('报告标题无法核验')
    parser = _LeafTables()
    parser.feed(html)
    tables = parser.tables
    if len(tables) == 16 and all((tables[i] == tables[i + 8] for i in range(8))):
        tables = tables[:8]
    if len(tables) != 8:
        raise RuntimeError('未识别八张工资统计表')
    out = []
    for i, t in enumerate(tables):
        if int(table) not in (0, i + 1):
            continue
        n = 2 if i < 5 else 3
        if len(t) <= n or not any(('单位' in c['text'] for c in t[0])):
            raise RuntimeError('第 %d 张表表头无法识别' % (i + 1))
        rows = [{'source_row': j + 1, 'cells': r} for j, r in enumerate(t) if j >= n and len(r) > 1 and (not keyword or any((keyword.replace(' ', '') in c['text'].replace(' ', '') for c in r)))]
        notes = [r for r in t[n:] if len(r) == 1]
        out.append({'table': i + 1, 'title': TITLES[i], 'header': t[:n], 'rows': rows, 'note_rows': notes})
    return {'source': '国家统计局城镇单位就业人员年平均工资情况', 'year': int(year), 'url': url, 'tables': out, 'note': '原表保留多行表头、单位与合并属性；为单位就业人员平均工资，不是个人工资中位数或全体劳动者收入，不同单位性质与职位口径不可直接混同。名义增速、可比口径及调查范围应核对官网正文。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--table', type=int, choices=range(9), default=0)
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.table, a.keyword), ensure_ascii=False, indent=2))
