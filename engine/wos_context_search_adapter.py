"""WOS Starter 主题、机构、国家地区及来源期刊的官方结构化检索。"""
import release_runtime
from clarivate_wos_starter_adapter import search as upstream_search

def search(keyword, field='topic', organization='', country='', journal='', author='', start=None, end=None, page=1, limit=5, sort_field=''):
    values = {'keyword': keyword, 'organization': organization, 'country': country, 'journal': journal, 'author': author}
    for name, value in values.items():
        if not isinstance(value, str) or len(value) > 300 or any((c in value for c in ('"', '\\', '\n', '\r'))) or any((ord(c) < 32 for c in value)):
            raise ValueError(name + ' 须为不含引号或控制字符的单行文本，最多 300 字')
    if not keyword.strip():
        raise ValueError('主题或标题不能为空')
    if field not in ('topic', 'title'):
        raise ValueError('field 须为 topic 或 title')
    if (start is None) != (end is None) or (start is not None and (type(start) is not int or type(end) is not int or (not 1900 <= start <= end <= 2100))):
        raise ValueError('发表年份应提供合法的起止年份')
    query = ('TS' if field == 'topic' else 'TI') + '=("' + keyword.strip() + '")'
    for tag, name in [('OG', 'organization'), ('CU', 'country'), ('SO', 'journal'), ('AU', 'author')]:
        if values[name].strip():
            query += ' AND ' + tag + '=("' + values[name].strip() + '")'
    if start is not None:
        query += ' AND PY=(' + str(start) + '-' + str(end) + ')'
    result = upstream_search(query, 'WOS', page, limit, sort_field=sort_field)
    result['structured_filters'] = {**{k: v.strip() or None for k, v in values.items()}, 'field': field, 'publication_year_range': [start, end] if start is not None else None}
    result['field_documentation'] = 'https://webofscience.help.clarivate.com/en-us/Content/wos-core-collection/woscc-search-field-tags.htm'
    result['note'] += ' OG 为机构增强字段，CU 为论文地址中的国家或地区，SO 为来源名称；多个条件按记录组合，不能推断指定作者属于指定机构或国家。年份可能匹配在线或最终出版年份；索引收录不等于全文授权。'
    return result
