"""低频刷新图书馆介绍页访问方式。中断后重新运行可续扫。"""
import release_runtime
import json, time, os
from datetime import date
from pathlib import Path
from research import catalog
from library_adapters import info
root = Path(__file__).resolve().parent
progress = root / '馆藏核对进度.json'
target = root / '浙大资源访问方式核对.json'
items = catalog()
try:
    verified = {x['id']: {k: x[k] for k in ('tested_browser_search', 'tested_cli', 'resource_classification') if k in x} for x in json.loads(target.read_text(encoding='utf-8'))['items']}
except (FileNotFoundError, KeyError, ValueError):
    verified = {}
try:
    saved = json.loads(progress.read_text(encoding='utf-8'))
except FileNotFoundError:
    saved = {}
for i, item in enumerate(items, 1):
    rid = item['id']
    if rid in saved:
        continue
    record = {k: item[k] for k in ('name', 'id', 'info_url', 'visit_url')}
    try:
        d = info(rid)
        record.update(on_campus=d['on_campus'], off_campus=d['off_campus'], status='介绍页已读取；业务接口未验证')
    except Exception as e:
        record.update(status='介绍页读取失败', error=str(e)[:180])
    if verified.get(rid):
        record.update(verified[rid])
    saved[rid] = record
    tmp = progress.with_suffix('.tmp')
    tmp.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, progress)
    print(f'{i}/{len(items)}', flush=True)
    time.sleep(2)
rows = [saved[item['id']] for item in items]
for record in rows:
    record.update(verified.get(record['id'], {}))
    if record['status'].startswith('介绍页已读取'):
        if 'tested_browser_search' in record:
            record['status'] = '介绍页已读取；已验证的浏览器功能范围见 tested_browser_search'
        elif 'tested_cli' in record:
            record['status'] = '介绍页已读取；已验证的命令行功能范围见 tested_cli'
out = {'date': date.today().isoformat(), 'source': 'https://libdb.zju.edu.cn/s/lib/libtb/', 'scope': '导航页条目的介绍页认证方式关键词，不代表业务接口及全文验证', 'total_entries': len(rows), 'success_count': sum((x['status'].startswith('介绍页已') for x in rows)), 'failure_count': sum((x['status'] == '介绍页读取失败' for x in rows)), 'items': rows}
tmp = target.with_suffix('.tmp')
tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
os.replace(tmp, target)
progress.unlink(missing_ok=True)
print('快照已更新；请检查失败项。', flush=True)
