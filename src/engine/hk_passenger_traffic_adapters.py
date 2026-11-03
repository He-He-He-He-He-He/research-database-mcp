"""香港入境事务处公开的每日出入境人次，按日期和管制站筛选。"""
import release_runtime
import argparse
import csv
import datetime as dt
import io
import json
import requests
URL = 'https://www.immd.gov.hk/opendata/hks/transport/immigration_clearance/statistics_on_daily_passenger_traffic.csv'
HEADERS = ['日期', '管制站', '入境 / 出境', '香港居民', '内地访客', '其他访客', '总计']

def passenger_traffic(date=None, station=None, timeout=20):
    if date is not None:
        dt.date.fromisoformat(date)
    if station is not None and (not isinstance(station, str) or len(station) > 50):
        raise ValueError('管制站名称无效')
    response = requests.get(URL, timeout=timeout)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.content.decode('utf-8-sig')))
    if reader.fieldnames != HEADERS:
        raise ValueError('官方 CSV 栏目已变化')
    items = []
    latest = None
    for row in reader:
        if not row['日期']:
            continue
        day = dt.datetime.strptime(row['日期'], '%d-%m-%Y').date().isoformat()
        if latest is None or day > latest:
            latest = day
            if date is None:
                items.clear()
        if (date or latest) != day or (station and row['管制站'] != station):
            continue
        items.append({'date': day, 'station': row['管制站'], 'direction': row['入境 / 出境'], 'hk_residents': row['香港居民'], 'mainland_visitors': row['内地访客'], 'other_visitors': row['其他访客'], 'total': row['总计']})
    return {'source': '香港入境事务处每日出入境人次统计', 'source_url': URL, 'date': date or latest, 'station_filter': station, 'items': items}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', help='YYYY-MM-DD，缺省为文件最新日期')
    parser.add_argument('--station', help='官方管制站名称')
    args = parser.parse_args()
    print(json.dumps(passenger_traffic(args.date, args.station), ensure_ascii=False, indent=2))
