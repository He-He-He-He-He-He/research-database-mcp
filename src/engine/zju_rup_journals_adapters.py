"""馆方 RUP 三刊介绍快照，不代表目前每篇访问权限。"""
import release_runtime
import json
_ROWS = [('The Journal of Cell Biology', '细胞生物学杂志', '0021-9525', '1540-8140', 'https://rupress.org/jcb'), ('The Journal of Experimental Medicine', '实验医学杂志', '0022-1007', '1540-9538', 'https://rupress.org/jem'), ('The Journal of General Physiology', '普通生理学杂志', '0022-1295', '1540-7748', 'https://rupress.org/jgp')]

def journals(keyword=''):
    if not isinstance(keyword, str):
        raise TypeError('keyword 必须为字符串')
    result = [{'title': t, 'chinese_title': c, 'print_issn': p, 'online_issn': e, 'url': u} for t, c, p, e, u in _ROWS if keyword.casefold() in (t + ' ' + c + ' ' + p + ' ' + e).casefold()]
    return {'source_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1599', 'snapshot_date': '2026-10-29', 'keyword': keyword, 'total_listed': len(_ROWS), 'matched': len(result), 'items': result, 'scope': '馆方历史说明列举的三刊，不代表全部 RUP 现刊、逐篇订购或全文权限。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    print(json.dumps(journals(p.parse_args().keyword), ensure_ascii=False, indent=2))
