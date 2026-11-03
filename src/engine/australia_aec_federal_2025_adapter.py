"""Australian Electoral Commission 2025 final result CSVs."""
import release_runtime
import csv, io
import requests
ROOT = 'https://results.aec.gov.au/31496/Website/Downloads/'
HOUSE = 'https://results.aec.gov.au/31496/Website/HouseDownloadsMenu-31496-Csv.htm'
SENATE = 'https://results.aec.gov.au/31496/Website/SenateDownloadsMenu-31496-Csv.htm'
TABLES = {'house-first-party': ('HouseFirstPrefsByParty', 'House first preferences by party'), 'house-tpp-division': ('HouseTppByDivision', 'House two-party preferred by division'), 'house-turnout-division': ('HouseTurnoutByDivision', 'House turnout by division'), 'senate-first-state': ('SenateFirstPrefsByStateByVoteType', 'Senate first preferences by state and voting method'), 'senate-elected': ('SenateSenatorsElected', 'Senators elected')}
NOTE = '澳大利亚选举委员会 2025 年联邦大选最终结果，原始表头与字符串保留，首行原始生成时间保留。众议院首选票、两党优先票、选区投票率与参议院结果的计算口径不同；首选票不等于最终席位。Bradfield 两党优先票为官方数学近似，不能当作直接实测计票。关键词仅在所选完整原表本地逐行匹配；表中可能有小计或总计。'

def table(name, keyword='', offset=0, limit=50, session=None):
    if name not in TABLES:
        raise ValueError('未知表名，可用：' + ', '.join(TABLES))
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('起始行须为非负整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('每页须为 1 至 1000 行')
    url = ROOT + TABLES[name][0] + 'Download-31496.csv'
    with (session or requests).get(url, headers={'Accept': '*/*', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=35, stream=True) as r:
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
    if len(rows) < 2 or len(rows[0]) != 1 or len(rows[1]) < 2:
        raise ValueError('官方 CSV 元信息或表头格式异常')
    text = keyword.strip().casefold()
    matched = [row for row in rows[2:] if not text or any((text in value.casefold() for value in row))]
    return {'source': 'Australian Electoral Commission, 2025 Federal Election', 'source_url': url, 'catalog': SENATE if name.startswith('senate-') else HOUSE, 'table': name, 'table_title': TABLES[name][1], 'raw_metadata': rows[0][0], 'note': NOTE, 'columns': rows[1], 'total_matched_rows': len(matched), 'offset': offset, 'limit': limit, 'rows': matched[offset:offset + limit]}
