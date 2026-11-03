"""FederalRegister.gov documents search and detail API."""
import release_runtime
import datetime
import re
import requests
BASE = 'https://www.federalregister.gov/api/v1/'

def search(term, agency=None, start_date=None, end_date=None, page=1, per_page=20, order='newest'):
    if not str(term).strip() or len(str(term)) > 300:
        raise ValueError('查询词须为 1–300 字符')
    if not 1 <= int(per_page) <= 100 or int(page) < 1:
        raise ValueError('per_page 须为 1–100，page 须为正整数')
    if order not in ('newest', 'oldest', 'relevance'):
        raise ValueError('排序限 newest、oldest、relevance')
    params = {'conditions[term]': term, 'per_page': int(per_page), 'page': int(page), 'order': order}
    if agency:
        if not re.fullmatch('[a-z0-9-]{1,100}', agency):
            raise ValueError('机构须使用官方英文 slug')
        params['conditions[agencies][]'] = agency
    for key, value in [('gte', start_date), ('lte', end_date)]:
        if value:
            datetime.date.fromisoformat(value)
            params['conditions[publication_date][' + key + ']'] = value
    r = requests.get(BASE + 'documents.json', params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def detail(document_number):
    if not re.fullmatch('[A-Za-z0-9-]{3,30}', str(document_number)):
        raise ValueError('无效公报文件编号')
    r = requests.get(BASE + 'documents/' + str(document_number) + '.json', timeout=30)
    r.raise_for_status()
    return r.json()
