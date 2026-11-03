"""ECDC ERVISS primary-care ILI / ARI consultation rates from public CSV."""
import release_runtime
import csv, hashlib, io, re
import requests
URL = 'https://raw.githubusercontent.com/EU-ECDC/Respiratory_viruses_weekly_data/main/data/ILIARIRates.csv'
INFO = 'https://github.com/EU-ECDC/Respiratory_viruses_weekly_data'

def query(country, week, indicator=None, age=None, limit=20, offset=0):
    if not isinstance(country, str) or not 1 <= len(country.strip()) <= 100:
        raise ValueError('Invalid country name')
    if not isinstance(week, str) or not re.fullmatch('\\d{4}-W(?:0[1-9]|[1-4][0-9]|5[0-3])', week):
        raise ValueError('Week must be YYYY-Www')
    if indicator is not None and indicator not in ('ILIconsultationrate', 'ARIconsultationrate'):
        raise ValueError('Invalid indicator')
    if age is not None and (not isinstance(age, str) or not re.fullmatch('[0-9+\\-a-z]{1,20}', age)):
        raise ValueError('Invalid age')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('Invalid pagination')
    with requests.get(URL, timeout=35, stream=True, allow_redirects=False) as r:
        if r.is_redirect or not r.ok:
            raise RuntimeError('ECDC repository returned HTTP ' + str(r.status_code))
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 6000000:
                raise RuntimeError('ECDC CSV exceeds 6 MB')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames != ['survtype', 'countryname', 'yearweek', 'indicator', 'age', 'value']:
        raise RuntimeError('Unexpected ECDC CSV columns')
    matched = []
    for row in reader:
        if row['countryname'].casefold() != country.strip().casefold() or row['yearweek'] != week:
            continue
        if indicator is not None and row['indicator'] != indicator:
            continue
        if age is not None and row['age'] != age:
            continue
        matched.append(row)
    return {'source': 'ECDC ERVISS primary-care syndromic consultation rates, official GitHub CSV', 'source_url': URL, 'source_info': INFO, 'file_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'selection': {'country': country, 'week': week, 'indicator': indicator, 'age': age, 'offset': offset, 'limit': limit}, 'matched_total': len(matched), 'items': matched[offset:offset + limit], 'note': 'ILI/ARI 症候群基层就诊率，并非实验室确认流感或全体感染率。通常每10万人，塞浦路斯、卢森堡、马耳他为每100次就诊，芬兰为每10万次就诊；跨国比较须核口径。数据可能修订。仓库 README 提示因数据迁移暂停 GitHub 更新并存在不一致，但 CSV 另含近期周次，时效以源文件及官方仪表盘核实；空结果非零。'}
