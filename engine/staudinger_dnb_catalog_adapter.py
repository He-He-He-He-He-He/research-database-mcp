"""German National Library bibliographic matches for the Staudinger commentary."""
import release_runtime
import re
import dnb_sru_adapters
SERIES = 'Staudingers Kommentar zum Bürgerlichen Gesetzbuch'
SERIES_QUERY = 'tit="' + SERIES + '"'

def search(keyword='', size=5, start=1):
    if not isinstance(keyword, str) or len(keyword) > 120:
        raise ValueError('关键词须为不超过 120 字的字符串')
    keyword = keyword.strip()
    if keyword and (not re.fullmatch('[\\w\\sÄÖÜäöüß§.,-]+', keyword, flags=re.UNICODE)):
        raise ValueError('关键词只能包含字母、数字、空格及常用标点')
    query = SERIES_QUERY
    if keyword:
        query += ' and tit="' + keyword + '"'
    result = dnb_sru_adapters.search(query, size, start)
    return {'source': '德国国家图书馆 DNB SRU 官方书目接口', 'series_query': SERIES, 'keyword': keyword, 'query': query, 'total': result['total'], 'start': result['start'], 'items': result['items'], 'scope': '按系列题名及可选标题关键词筛选相关书目；出版年份可能包含未来计划版本。结果不是在线版全文或浙大馆藏订购清单，不能证明对应条目已收录或获授权。', 'related_collection': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1915', 'publisher_information': 'https://www.juris.de/jportal/nav/produkte/werk/staudinger-online-powered-by-juris-buch-1-allgemeiner-teil.jsp'}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--size', type=int, default=5)
    p.add_argument('--start', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.size, a.start), ensure_ascii=False, indent=2))
