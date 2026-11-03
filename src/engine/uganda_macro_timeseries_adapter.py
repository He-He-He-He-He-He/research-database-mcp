"""Uganda finance ministry's published read-only UGATSDB time-series database."""
import release_runtime
import argparse, json, os, re, sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / '.vendor'))
import pymysql, requests
from pymysql.cursors import DictCursor
PUBLIC_CLIENT = 'https://raw.githubusercontent.com/cran/ugatsdb/master/R/ugatsdb.R'

def _connect():
    pw = release_runtime.environment.get('UGATSDB_PUBLIC_PASSWORD')
    if not pw:
        r = requests.get(PUBLIC_CLIENT, timeout=20)
        r.raise_for_status()
        m = re.search("user = 'MEPD_READ', password = '([^']+)'", r.text)
        if not m:
            raise ValueError('Public client credential format changed; set UGATSDB_PUBLIC_PASSWORD')
        pw = m.group(1)
    return pymysql.connect(host='154.72.200.20', port=3306, user='MEPD_READ', password=pw, database='UGATSDB', connect_timeout=10, read_timeout=20, cursorclass=DictCursor)

def _query(sql, params):
    c = _connect()
    try:
        with c.cursor() as q:
            q.execute(sql, params)
            return [{k: v.isoformat() if isinstance(v, (date, datetime)) else str(v) if isinstance(v, Decimal) else v for k, v in row.items()} for row in q.fetchall()]
    finally:
        c.close()

def search(keyword, limit=20):
    if not keyword or len(keyword) > 100 or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    query = 'SELECT DSID,Series,Label,S_From,S_To,S_Source,S_Url FROM SERIES WHERE Label LIKE %s ORDER BY DSID,Series LIMIT %s'
    return {'source': 'Uganda Ministry of Finance UGATSDB SERIES', 'results': _query(query, ('%' + keyword + '%', limit))}

def metadata(dataset, series):
    if not re.fullmatch('[A-Za-z0-9_]{1,30}', dataset) or not re.fullmatch('[A-Za-z0-9_]{1,30}', series):
        raise ValueError('invalid dataset or series')
    rows = _query('SELECT s.DSID,s.Series,s.Label,s.S_From,s.S_To,s.S_Source,s.S_Url,d.Dataset,d.Frequency,d.Updated,d.Source,d.DS_Url FROM SERIES s JOIN DATASET d ON s.DSID=d.DSID WHERE s.DSID=%s AND s.Series=%s', (dataset, series))
    if not rows:
        raise ValueError('series not found')
    return {'source': 'Uganda Ministry of Finance UGATSDB', 'metadata': rows[0]}

def data(dataset, series, limit=20):
    if not 1 <= limit <= 100:
        raise ValueError('limit 1–100')
    m = metadata(dataset, series)['metadata']
    rows = _query('SELECT Date,Value FROM DATA WHERE DSID=%s AND Series=%s ORDER BY Date DESC LIMIT %s', (dataset, series, limit))
    return {'source': 'Uganda Ministry of Finance UGATSDB', 'metadata': m, 'results': rows, 'note': '日期编码和单位必须按数据集频率及标签解释。'}

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('search')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=20)
    a = s.add_parser('metadata')
    a.add_argument('dataset')
    a.add_argument('series')
    a = s.add_parser('data')
    a.add_argument('dataset')
    a.add_argument('series')
    a.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.dataset, a.series) if a.cmd == 'metadata' else data(a.dataset, a.series, a.limit)
    print(json.dumps(x, ensure_ascii=False, default=str, indent=2))
if __name__ == '__main__':
    main()
