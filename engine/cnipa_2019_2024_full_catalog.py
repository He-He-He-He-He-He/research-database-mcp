"""CNIPA official annual statistics 2019–2024: catalog and original HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin
from cnipa_2025_full_catalog import Links, fetch
from cnipa_stats_adapters import Tables

def catalog(year, keyword='', group=''):
    if type(year) is not int or year not in range(2019, 2025):
        raise ValueError('year must be 2019–2024')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if not isinstance(group, str) or (group and (not re.fullmatch('[a-i]', group))):
        raise ValueError('invalid group')
    root = f'https://www.cnipa.gov.cn/tjxx/jianbao/year{year}/'
    top = Links('[a-i]\\.html')
    top.feed(fetch(root + 'indexy.html'))
    if not top.links:
        raise RuntimeError('无法识别年度目录')
    available = [href[0] for href, title in top.links]
    if group and group not in available:
        raise ValueError('该年度不含该分组')
    items = []
    errors = []
    for href, gtitle in top.links:
        g = href[0]
        if group and group != g:
            continue
        try:
            links = Links(g + '/' + g + '\\d+\\.html')
            links.feed(fetch(urljoin(root, href)))
            if not links.links:
                raise RuntimeError('分组页面未识别条目')
            for path, title in links.links:
                if keyword in title:
                    items.append({'code': path.rsplit('/', 1)[-1][:-5], 'title': title, 'group': g, 'group_title': gtitle, 'url': urljoin(root, path)})
        except (RuntimeError, UnicodeError) as exc:
            errors.append({'group': g, 'error': str(exc)})
    return {'source': f'国家知识产权局{year}年知识产权统计年报', 'year': year, 'catalog_url': root + 'indexy.html', 'count': len(items), 'items': items, 'errors': errors, 'note': '按官方目录实时读取；分组错误表示目录不完整。年度为年报年份，具体数据年份和统计口径以原表为准。'}

def detail(year, code):
    if not isinstance(code, str) or not re.fullmatch('[a-i]\\d+', code):
        raise ValueError('invalid code')
    listing = catalog(year, group=code[0])
    if listing['errors']:
        raise RuntimeError('分组目录未能核验')
    match = next((x for x in listing['items'] if x['code'] == code), None)
    if match is None:
        raise ValueError('该年官方目录中不存在该表编号')
    parser = Tables()
    parser.feed(fetch(match['url']))
    table = max(parser.tables, key=len, default=[])
    if len(table) < 3:
        raise RuntimeError('未识别有效表格')
    return {'source': listing['source'], 'year': year, 'code': code, 'title': match['title'], 'url': match['url'], 'rows': table, 'note': '保留原表合并单元格信息；原网页的单位、表下注释和统计口径须另行核查。年报年份与表中统计年份不必相同，不自动拼接跨年。'}
