"""全球案例发现系统校园 IP 单条案例素材详情。"""
import release_runtime
import requests
from htcases_institution_catalog_adapter import _config, _post, _require_institution

def detail(item_id, expected_title):
    if isinstance(item_id, bool) or not str(item_id).isdigit() or (not 1 <= int(item_id) <= 999999999999):
        raise ValueError('案例编号须为正整数')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整标题')
    with requests.Session() as s:
        config = _config(s)
        _require_institution(s,config)
        row = _post(s, 'lib/metadata/get', {'id': int(item_id)}, config).get('body')
    if not isinstance(row, dict) or type(row.get('id')) is not int or row['id'] != int(item_id) or (row.get('title') != expected_title.strip()):
        raise RuntimeError('站方案例编号或标题不匹配')
    fields = ('id', 'title', 'author', 'source', 'publicationDate', 'caseLibName', 'caseLibType', 'language', 'keyword', 'contentBrief', 'learningObjective', 'intendedAudience', 'contentIndustries')
    return {'source': '全球案例发现系统', 'institution': '浙江大学（IP）', 'item': {k: row.get(k) for k in fields}, 'note': '站方素材详情字段，保留简介、学习目标、关键词及日期原始值；部分素材为新闻，不代表完整教学案例、全文或下载权限。'}
