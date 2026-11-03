"""香港政府 DATA.GOV.HK 官方 CKAN 数据集元数据接口。"""
import release_runtime
import re
import requests
BASE = 'https://data.gov.hk/{lang}-data/api/3/action/'
LANGS = {'sc', 'tc', 'en'}

def _call(action, params=None, lang='sc'):
    if lang not in LANGS:
        raise ValueError('语言须为 sc、tc 或 en')
    if action not in ('package_list', 'package_show', 'group_list', 'group_show'):
        raise ValueError('不支持的目录方法')
    response = requests.get(BASE.format(lang=lang) + action, params=params, timeout=45, allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect:
        raise RuntimeError('目录服务重定向')
    try:
        obj = response.json()
    except ValueError as exc:
        raise RuntimeError('目录服务返回非 JSON') from exc
    if not isinstance(obj, dict) or obj.get('success') is not True or 'result' not in obj:
        raise RuntimeError('目录服务未成功返回结果')
    return obj['result']

def dataset_ids(keyword='', lang='sc'):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字符')
    values = _call('package_list', lang=lang)
    if not isinstance(values, list) or not all((isinstance(x, str) for x in values)):
        raise RuntimeError('数据集 ID 列表异常')
    items = [x for x in values if keyword.casefold() in x.casefold()]
    return {'source': '香港政府 DATA.GOV.HK', 'language': lang, 'catalog_total': len(values), 'matched_count': len(items), 'items': items, 'note': '关键词仅本地匹配数据集 ID，不搜索中文标题或文件内容；ID 未命中不代表没有相关数据。'}

def dataset(identifier, lang='sc'):
    if not isinstance(identifier, str) or not re.fullmatch('[a-zA-Z0-9_-]{1,150}', identifier):
        raise ValueError('请输入数据集 ID')
    result = _call('package_show', {'id': identifier}, lang)
    if not isinstance(result, dict) or not result.get('name') or (not isinstance(result.get('resources'), list)):
        raise RuntimeError('数据集元数据结构异常')
    return {'source': '香港政府 DATA.GOV.HK', 'language': lang, 'metadata': result, 'note': '这是数据集元数据及来源链接，不代表具体文件已下载、可用或免费；各资源的许可与使用条件须单独核验。'}

def groups(lang='sc'):
    result = _call('group_list', lang=lang)
    if not isinstance(result, list) or not all((isinstance(x, str) for x in result)):
        raise RuntimeError('主题列表异常')
    return {'source': '香港政府 DATA.GOV.HK', 'language': lang, 'items': result}

def group(identifier, lang='sc'):
    if not isinstance(identifier, str) or not re.fullmatch('[a-zA-Z0-9_-]{1,150}', identifier):
        raise ValueError('请输入主题 ID')
    result = _call('group_show', {'id': identifier}, lang)
    if not isinstance(result, dict) or not result.get('name'):
        raise RuntimeError('主题元数据异常')
    return {'source': '香港政府 DATA.GOV.HK', 'language': lang, 'metadata': {k: result.get(k) for k in ('name', 'title', 'description', 'package_count', 'state')}, 'note': 'package_count 为官网主题关联数据集数；不代表所有资源已验证可用。'}
