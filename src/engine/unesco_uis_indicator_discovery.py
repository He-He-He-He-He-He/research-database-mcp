"""检索 UNESCO UIS 官方指标目录；关键词按代码/英文名称本地匹配。"""
import release_runtime
import argparse, json, subprocess
URL = 'https://api.uis.unesco.org/api/public/definitions/indicators'

def search_indicators(keyword, theme='', limit=20, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword 不可为空')
    if not isinstance(theme, str) or not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('theme、limit 或 offset 无效')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', URL], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('UIS 指标目录请求失败')
    data = json.loads(p.stdout)
    if not isinstance(data, list) or any((not isinstance(x, dict) for x in data)):
        raise RuntimeError('UIS 指标目录格式异常')
    q = keyword.casefold().strip()
    t = theme.casefold().strip()
    hits = [x for x in data if q in (str(x.get('indicatorCode', '')) + ' ' + str(x.get('name', ''))).casefold() and (not t or t in str(x.get('theme', '')).casefold())]
    return {'source': 'UNESCO UIS official indicator definitions', 'source_url': URL, 'keyword': keyword, 'theme': theme, 'matched': len(hits), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(hits) else None, 'items': hits[offset:offset + limit], 'scope': '每次重新获取官方目录并本地截取，跨请求目录可能更新；按代码及英文名称本地匹配官方完整目录，availability 为指标总体时间和地域，不保证指定国家有数据；用 indicatorCode 再查询具体国家。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--theme', default='')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(search_indicators(a.keyword, a.theme, a.limit, offset=a.offset), ensure_ascii=False, indent=2))
