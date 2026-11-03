"""WOS Starter 各产品数据库的主题、作者和发表年份检索。"""
import release_runtime
from clarivate_wos_starter_adapter import search as upstream, DATABASES

def search(database, keyword, field='topic', author='', start=None, end=None, page=1, limit=5):
    if database not in DATABASES:
        raise ValueError('数据库代码不受支持')
    for name, value in [('keyword', keyword), ('author', author)]:
        if not isinstance(value, str) or len(value) > 300 or any((c in value for c in ('"', '\\', '\n', '\r'))) or any((ord(c) < 32 for c in value)):
            raise ValueError(name + ' 须为不含引号和控制字符的单行文本，最多 300 字')
    if not keyword.strip():
        raise ValueError('主题或标题不能为空')
    if field not in ('topic', 'title'):
        raise ValueError('field 须为 topic 或 title')
    if (start is None) != (end is None) or (start is not None and (type(start) is not int or type(end) is not int or (not 1900 <= start <= end <= 2100))):
        raise ValueError('发表年应提供合法的起止年份')
    q = ('TS' if field == 'topic' else 'TI') + '=("' + keyword.strip() + '")'
    if author.strip():
        q += ' AND AU=("' + author.strip() + '")'
    if start is not None:
        q += ' AND PY=(' + str(start) + '-' + str(end) + ')'
    out = upstream(q, database, page, limit)
    out['structured_filters'] = {'database': database, 'keyword': keyword.strip(), 'field': field, 'author': author.strip() or None, 'publication_year_range': [start, end] if start is not None else None}
    out['note'] += ' 数据库和字段的可用性由实际订阅与上游决定；空结果不能单独证明不存在或已授权。不同库数据范围和字段语义可能不同，年份可能包含早期在线年份；同名作者须消歧。'
    if database == 'DIIDW':
        out['note'] += ' DIIDW 2026-11-02 样例中，筛选 2020–2023 返回记录 source.publishYear 为 2019，来源日期匹配口径尚未核清，暂不能信赖按年筛选；部分详情不含专利号，不能据此确认专利法律状态。'
    return out
