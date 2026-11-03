"""IATI Datastore official Solr query using the local Keychain subscription."""
import release_runtime
import subprocess
import requests
BASE = 'https://api.iatistandard.org/datastore/'

def query(collection, q, rows=10, start=0):
    if collection not in ('activity', 'transaction', 'budget'):
        raise ValueError('collection must be activity, transaction or budget')
    if not isinstance(q, str) or not 1 <= len(q.strip()) <= 300:
        raise ValueError('q must contain 1–300 characters')
    if type(rows) is not int or not 1 <= rows <= 100 or type(start) is not int or (not 0 <= start <= 100000):
        raise ValueError('invalid rows or start')
    key = release_runtime.run(['security', 'find-generic-password', '-a', 'zju-research-toolkit', '-s', 'research-toolkit-iati-exploratory', '-w'], capture_output=True, text=True, check=True, timeout=60).stdout.strip()
    r = requests.get(BASE + collection + '/select', params={'q': q, 'rows': rows, 'start': start, 'wt': 'json'}, headers={'Ocp-Apim-Subscription-Key': key}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('response'), dict) or not isinstance(data['response'].get('docs'), list):
        raise ValueError('unexpected IATI response')
    return {'source': 'IATI Datastore', 'source_url': BASE + collection + '/select', 'collection': collection, 'query': q, 'data': data['response'], 'note': 'IATI 是发布者自愿报告的数据，并非完整官方发展援助；活动、交易、预算口径不同，不应直接加总。免费订阅限每秒1次、每天500次。'}
