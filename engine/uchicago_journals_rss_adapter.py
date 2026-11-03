"""University of Chicago Press journal RSS catalog, current articles only."""
import release_runtime
import subprocess, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
import openpyxl
PATH = release_runtime.home() / 'Library/Application Support/ResearchDatabaseToolkit/uchicago/rss_feeds_2026-01.xlsx'
INFO = 'https://www.journals.uchicago.edu/kbart'
R = '{http://purl.org/rss/1.0/}'
D = '{http://purl.org/dc/elements/1.1/}'
P = '{http://prismstandard.org/namespaces/basic/2.0/}'

def catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词无效')
    wb = openpyxl.load_workbook(PATH, read_only=True, data_only=True)
    out = []
    try:
        for row in wb.active.iter_rows(values_only=True):
            title, url = (row[0], row[1])
            if not isinstance(title, str) or not isinstance(url, str) or keyword.casefold() not in title.casefold():
                continue
            u = urllib.parse.urlsplit(url)
            q = urllib.parse.parse_qs(u.query)
            if u.scheme != 'https' or u.netloc != 'www.journals.uchicago.edu' or u.path != '/action/showFeed' or (q.get('type') != ['etoc']) or (q.get('feed') != ['rss']) or (len(q.get('jc', [])) != 1):
                continue
            out.append({'title': title.strip(), 'code': q['jc'][0], 'url': url})
    finally:
        wb.close()
    return {'source': 'University of Chicago Press official RSS catalog', 'source_url': INFO, 'snapshot': '2026-01 official list; downloaded 2026-10-30', 'matches': len(out), 'items': out, 'note': '已列刊名不等于订购或 RSS 实时可用；已抽验 ajs、jpe、jle、aje、ca、eh 六刊，其余未逐一验证。'}

def search(code, keyword='', offset=0, limit=20):
    if not isinstance(code, str) or not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('输入无效')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    matches = [x for x in catalog()['items'] if x['code'] == code]
    if len(matches) != 1:
        raise ValueError('期刊代码未在官方目录中唯一匹配')
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '4000000', matches[0]['url']], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('RSS unavailable: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise ValueError('RSS too large')
    root = ET.fromstring(p.stdout)
    ch = root.find(R + 'channel')
    if ch is None:
        raise ValueError('Unexpected RSS format')
    journal = ch.findtext(P + 'publicationName') or ch.findtext(R + 'title') or ''
    source_items = root.findall(R + 'item')
    results = []
    for x in source_items:
        val = lambda tag: ' '.join((x.findtext(tag) or '').split())
        item = {'title': val(R + 'title'), 'url': val(R + 'link'), 'doi': val(P + 'doi'), 'creator_raw': [v.text.strip() for v in x.findall(D + 'creator') if v.text and v.text.strip()], 'date': val(D + 'date'), 'volume': val(P + 'volume'), 'issue': val(P + 'number'), 'cover_date': val(P + 'coverDate')}
        if item['title'] and keyword.casefold() in (item['title'] + ' ' + ' '.join(item['creator_raw'])).casefold():
            results.append(item)
    return {'source': 'University of Chicago Press journal RSS', 'source_url': matches[0]['url'], 'catalog_title': matches[0]['title'], 'feed_title': journal, 'feed_title_matches_catalog': journal.casefold().strip() == matches[0]['title'].casefold().strip(), 'feed_records': len(source_items), 'keyword': keyword, 'matches': len(results), 'offset': offset, 'limit': limit, 'items': results[offset:offset + limit], 'note': '仅当前源的文章题录，本地标题与作者字段包含检索；不代表历史全库、浙大订购或全文。creator 原始值可能粘连多个作者与机构，日期须核原文；频道标题与目录不一致时应先核对。'}
