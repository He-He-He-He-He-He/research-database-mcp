"""Elections Canada 45th general election official summary CSV tables."""
import release_runtime
import csv, io
import requests
BASE = 'https://www.elections.ca/res/rep/off/ovrGE45/62/data_donnees/table_tableau{:02d}.csv'
CATALOG = 'https://www.elections.ca/content.aspx?dir=rep%2Foff%2F45gedata&document=summary&lang=e&section=res'
TABLES = {1: 'Number of electors and polls', 2: 'Electors and polls: 2025, 2021, 2019, 2015', 3: 'Ballots and voter turnout', 4: 'Voter turnout: 2025, 2021, 2019, 2015', 5: 'Valid votes by voting method', 6: 'Valid votes under special voting rules', 7: 'Seats by political affiliation and gender', 8: 'Valid votes by political affiliation', 9: 'Valid vote percentage by political affiliation', 10: 'Candidates by vote percentage and affiliation', 11: 'Voting results by electoral district', 12: 'Candidates and individual results'}
NOTE = '加拿大 2025 年第 45 届联邦大选官方结果，按原始 CSV 双语表头及每行字符串保留；地方选区经过重新划分，与此前名称相似的选区不一定地理等同。有效票数、总投票数、合格选民数、席位及百分比的分母与口径不同；不应互换或直接推算。原表可能包含总计或注释行；关键词筛选仅对当前完整原表做逐行文本匹配，非服务端筛选。'

def table(number, keyword='', offset=0, limit=50, session=None):
    if isinstance(number, bool) or number not in TABLES:
        raise ValueError('表号须为 1 至 12')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('起始行须为非负整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('每页须为 1 至 1000 行')
    with (session or requests).get(BASE.format(number), headers={'Accept': '*/*', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > 8 * 1024 * 1024:
                raise ValueError('原始 CSV 超过 8 MiB')
        url = r.url
    try:
        rows = list(csv.reader(io.StringIO(bytes(b).decode('utf-8-sig'), newline='')))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError('官方 CSV 解析失败') from exc
    if not rows or not rows[0]:
        raise ValueError('官方 CSV 无表头')
    text = keyword.strip().casefold()
    matched = [row for row in rows[1:] if not text or any((text in value.casefold() for value in row))]
    return {'source': 'Elections Canada, 45th General Election, official voting results', 'source_url': url, 'catalog': CATALOG, 'table_number': number, 'table_title': TABLES[number], 'note': NOTE, 'columns': rows[0], 'total_matched_rows': len(matched), 'offset': offset, 'limit': limit, 'rows': matched[offset:offset + limit]}
