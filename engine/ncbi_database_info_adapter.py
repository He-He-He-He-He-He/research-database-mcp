"""NCBI EInfo database search fields and linked database metadata."""
import release_runtime
import re
from ncbi_entrez_adapters import _get

def info(database, keyword='', limit=50, offset=0):
    if not isinstance(database, str) or not re.fullmatch('[A-Za-z0-9_]{1,40}', database):
        raise ValueError('invalid Entrez database name')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 200) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword or pagination')
    j = _get('einfo', {'db': database})
    entries = (j.get('einforesult') or {}).get('dbinfo') if isinstance(j, dict) else None
    if not isinstance(entries, list) or len(entries) != 1 or (not isinstance(entries[0], dict)) or (str(entries[0].get('dbname', '')).casefold() != database.casefold()):
        raise RuntimeError('NCBI EInfo returned mismatched database')
    d = entries[0]
    fields = d.get('fieldlist')
    links = d.get('linklist')
    if not isinstance(fields, list) or not isinstance(links, list) or any((not isinstance(x, dict) for x in fields + links)):
        raise RuntimeError('unexpected EInfo fields or links')
    q = keyword.casefold()
    filtered = [x for x in fields if q in (str(x.get('name', '')) + ' ' + str(x.get('fullname', '')) + ' ' + str(x.get('description', ''))).casefold()]
    return {'source': 'NCBI EInfo', 'documentation': 'https://www.ncbi.nlm.nih.gov/books/NBK25499/', 'database': d.get('dbname'), 'description': d.get('description'), 'database_count_raw': d.get('count'), 'lastupdate': d.get('lastupdate'), 'dbbuild': d.get('dbbuild'), 'keyword': keyword, 'matched_fields': len(filtered), 'offset': offset, 'next_offset': offset + limit if offset + limit < len(filtered) else None, 'fields': filtered[offset:offset + limit], 'links': links, 'note': '字段名与说明来自当前官方 EInfo，可用于构造 NCBI 搜索式；字段存在不代表每条记录均有内容。数据库统计及结构可能更新，详情依数据库类型而异。'}
