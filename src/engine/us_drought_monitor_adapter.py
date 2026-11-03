"""U.S. Drought Monitor weekly state area percentages."""
import release_runtime
import datetime
import json
import requests
URL = 'https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent'
FIPS = set('01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56 60 66 69 72 78'.split())

def query(fips, start, end, format='traditional'):
    if not isinstance(fips, str) or fips not in FIPS:
        raise ValueError('Use a two-digit state or territory FIPS code')
    if format not in ('traditional', 'categorical'):
        raise ValueError('Invalid statistics format')
    try:
        lo = datetime.date.fromisoformat(start)
        hi = datetime.date.fromisoformat(end)
    except (TypeError, ValueError):
        raise ValueError('Dates must be ISO YYYY-MM-DD') from None
    if start != lo.isoformat() or end != hi.isoformat() or lo > hi or ((hi - lo).days > 366 * 5):
        raise ValueError('Invalid date range; maximum five years')
    p = {'aoi': fips, 'startdate': lo.strftime('%m/%d/%Y'), 'enddate': hi.strftime('%m/%d/%Y'), 'statisticsType': 1 if format == 'traditional' else 2}
    with requests.get(URL, params=p, headers={'Accept': 'application/json'}, timeout=30, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('USDM service returned HTTP ' + str(response.status_code))
        body = bytearray()
        for part in response.iter_content(65536):
            body.extend(part)
            if len(body) > 2000000:
                raise RuntimeError('USDM response exceeds 2 MB')
    data = json.loads(body)
    if not isinstance(data, list) or any((not isinstance(x, dict) or x.get('statisticFormatID') != p['statisticsType'] for x in data)):
        raise RuntimeError('Unexpected USDM response')
    return {'source': 'U.S. Drought Monitor state weekly area percentage', 'source_info': 'https://droughtmonitor.unl.edu/DmData/DataDownload/WebServiceInfo.aspx', 'source_url': URL, 'selection': {'state_fips': fips, 'start': start, 'end': end, 'format': format}, 'returned': len(data), 'items': data, 'note': '百分比是地区面积占比，不是人口占比。traditional 的 D0–D4 为该级及更严重级别的累计面积，不能相加；categorical 各级互斥。D0 为异常干燥，D1–D4 为不同严重程度干旱。地图每周更新、反映当时监测及专家分析而非预测；空结果不等于零。'}
