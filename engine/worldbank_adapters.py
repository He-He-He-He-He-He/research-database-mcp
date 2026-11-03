"""World Bank Indicators API: country lookup, indicator metadata and series."""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
ROOT = 'https://api.worldbank.org/v2'

def _get(path, params=None):
    args = {'format': 'json', **(params or {})}
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', ROOT + path + '?' + urlencode(args)], capture_output=True)
    if p.returncode:
        raise RuntimeError(f'世界银行请求失败 (curl 状态 {p.returncode})')
    data = json.loads(p.stdout)
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and isinstance(data[0].get('message'), list):
        messages = data[0]['message']
        detail = '; '.join((str(item.get('value') or item.get('key') or 'unknown error') for item in messages if isinstance(item, dict)))
        raise ValueError('世界银行 API 错误：' + (detail or '未知错误'))
    if not isinstance(data, list) or len(data) != 2 or (not isinstance(data[0], dict)):
        raise ValueError('世界银行响应错误或格式变化')
    if not isinstance(data[1], list):
        raise ValueError('未找到数据')
    return data

def countries(query):
    if not query or not query.strip():
        raise ValueError('国家或地区关键词不能为空')
    meta, rows = _get('/country', {'per_page': 400})
    if meta.get('pages', 1) > 1:
        raise ValueError('国家目录超过单页，需更新实现')
    q = query.casefold().strip()
    hits = [x for x in rows if q in x.get('name', '').casefold() or q == x.get('id', '').casefold() or q == x.get('iso2Code', '').casefold()]
    return {'query': query, 'matches': len(hits), 'items': hits}

def indicator(code):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,64}', code):
        raise ValueError('指标代码格式不合法')
    data = _get('/indicator/' + code)
    if not data[1]:
        raise ValueError('未找到指标')
    return data

def series(country, code, start, end, source=None, max_pages=4, page=1):
    countries=list(dict.fromkeys(re.split('[,;]',country)))
    codes=list(dict.fromkeys(re.split('[,;]',code)))
    if not 1<=len(countries)<=20 or any(not re.fullmatch('[A-Za-z]{2,3}',x) for x in countries):
        raise ValueError('国家代码须为2或3个字母，逗号或分号分隔，最多20个')
    if not 1<=len(codes)<=10 or any(not re.fullmatch('[A-Za-z0-9_.-]{1,64}',x) for x in codes):
        raise ValueError('指标代码格式不合法；最多10个，用逗号或分号分隔')
    if type(max_pages) is not int or not 1<=max_pages<=10:raise ValueError('max_pages须1至10')
    if type(page) is not int or not 1<=page<=1000:raise ValueError('page须1至1000')
    if source is not None and not re.fullmatch('[0-9]{1,5}',str(source)):raise ValueError('source须为官方数据源编号')
    if not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围不合法')
    path='/country/'+';'.join(countries)+'/indicator/'+';'.join(codes)
    params={'date':f'{start}:{end}','per_page':1000,'page':page}
    if source is not None or len(codes)>1:params['source']=str(source or 2)
    meta,rows=_get(path,params);pages=int(meta.get('pages',1));fetched=1;last_page=page
    if page>pages and pages>0:raise ValueError('page超过源站总页数')
    # Preserve the existing [metadata, rows] shape; never pretend a bounded scan
    # has fetched every upstream page or fill missing values with zero.
    failed=[]
    for following in range(page+1,min(pages,page+max_pages-1)+1):
        try:
            more_meta,more=_get(path,{**params,'page':following})
            if int(more_meta.get('page',following))!=following or int(more_meta.get('total',meta.get('total',0)))!=int(meta.get('total',0)):raise ValueError('分页元数据在请求间变化')
            rows.extend(more);fetched+=1;last_page=following
        except Exception as exc:
            failed.append({'page':following,'error':type(exc).__name__});break
    meta={**meta,'pages_fetched':fetched,'complete':page==1 and last_page==pages and not failed,'next_page':last_page+1 if last_page<pages else None,'previous_pages_omitted':page-1,'requested_countries':countries,'requested_indicators':codes,'failed_pages':failed}
    return [meta,rows]

def main():
    p = argparse.ArgumentParser(description='世界银行公开指标数据')
    sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('countries')
    s.add_argument('query')
    d = sp.add_parser('indicator')
    d.add_argument('code')
    v = sp.add_parser('series')
    v.add_argument('country')
    v.add_argument('code')
    v.add_argument('--start', type=int, required=True)
    v.add_argument('--end', type=int, required=True)
    v.add_argument('--source', default=None)
    v.add_argument('--max-pages',type=int,default=4)
    v.add_argument('--page',type=int,default=1)
    a = p.parse_args()
    try:
        result = countries(a.query) if a.cmd == 'countries' else indicator(a.code) if a.cmd == 'indicator' else series(a.country, a.code, a.start, a.end,a.source,a.max_pages,a.page)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
