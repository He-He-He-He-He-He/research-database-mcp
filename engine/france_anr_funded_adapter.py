"""ANR open DGDS project data via the French government's data.gouv.fr tabular API."""
import release_runtime
import re
import requests
DATASET = 'https://www.data.gouv.fr/api/1/datasets/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/'
TABLE = 'https://tabular-api.data.gouv.fr/api/resources/{}/data/'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}

def search(keyword='', language='english', period='since2010', page=1, page_size=10, session=None):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词无效')
    if language not in ('english', 'french') or period not in ('since2010', '2005to2009'):
        raise ValueError('语言或年份范围无效')
    if type(page) is not int or page < 1 or type(page_size) is not int or (not 1 <= page_size <= 100):
        raise ValueError('页码或每页数量无效')
    client = session or requests
    metadata = client.get(DATASET, headers=HEADERS, timeout=25)
    metadata.raise_for_status()
    meta = metadata.json()
    pattern = '^anr-dgds-' + ('depuis-2010' if period == 'since2010' else '2005-2009') + '-projets-finances-\\d{8}-projets\\.csv$'
    matching = [x for x in meta.get('resources', []) if isinstance(x, dict) and re.fullmatch(pattern, x.get('title', ''), re.I) and re.fullmatch('[0-9a-f-]{36}', x.get('id', ''), re.I)]
    if len(matching) != 1:
        raise ValueError('未能唯一确定当前 ANR 项目数据文件，请检查官方目录')
    resource = matching[0]
    params = {'page': page, 'page_size': page_size}
    if keyword.strip():
        params['Projet.Titre.' + ('Anglais' if language == 'english' else 'Francais') + '__contains'] = keyword.strip()
    r = client.get(TABLE.format(resource['id']), params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get('data'), list) or (not isinstance(data.get('meta'), dict)):
        raise ValueError('表格接口返回格式异常')
    return {'source': 'Agence nationale de la recherche, data.gouv.fr', 'dataset_url': 'https://www.data.gouv.fr/datasets/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/', 'resource_id': resource['id'], 'resource_title': resource['title'], 'resource_last_modified': resource.get('last_modified'), 'query': params, 'note': '仅检索所选年份范围的 DGDS 项目；按所选语言的标题包含关系检索，不是全文检索。原表金额、缺失值和项目范围原样保留，未合并其他资助计划或参与方表。', 'data': data}
