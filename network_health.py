"""Lazy, expiring network skips based on actual transport failures.

Do not infer reachability from country, proxy presence, HTTP 403 or 429.
Only a failed query records a short cooldown; no background probes or routing changes.
"""
import json
import os
import tempfile
import time
from urllib.parse import urlsplit
import release_runtime as rt

COOLDOWN = 60
KINDS = {'network_dns_error','network_connection_error','network_proxy_error',
         'network_tls_error','upstream_timeout'}


def _load():
    try:
        data = json.loads((rt.state_root()/'network-health.json').read_text(encoding='utf-8'))
        if not isinstance(data,dict): return {}
        return {k:v for k,v in data.items() if k.startswith('command:') and isinstance(v,dict) and v.get('reason') in KINDS and isinstance(v.get('retry_at'),(int,float)) and v['retry_at'] > time.time()}
    except (FileNotFoundError,ValueError,OSError): return {}


def _save(data):
    root = rt.state_root(); root.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd, name = tempfile.mkstemp(dir=root,prefix='.network-',text=True)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream: json.dump(data,stream)
        os.replace(name,root/'network-health.json')
    finally:
        if os.path.exists(name): os.unlink(name)


def status():
    return {'auto_skip':True,'cooldown_seconds':COOLDOWN,'unavailable':_load(),
            'notice':'仅根据真实连接失败短暂跳过；未检查不等于可达。不因国外来源或缺少代理而一概跳过。'}


def reset():
    _save({})
    return status()


def blocked(entry):
    data = _load()
    # Static host hints are not used to suppress unrelated queries: namespaces and
    # documentation can share hosts without being the actual query destination.
    return data.get('command:'+entry['command'])


def record(entry, result):
    error = result.get('error')
    if error not in KINDS: return result
    details = result.get('diagnostics') or {}
    endpoint = details.get('endpoint')
    try: host = urlsplit(endpoint).hostname if endpoint else None
    except ValueError: host = None
    data = _load()
    info = {'reason':error,'retry_at':int(time.time())+COOLDOWN}
    if host: info['host'] = host
    data['command:'+entry['command']] = info
    _save(data)
    return {**result,'skipped':True,'skip_reason':'network_unavailable',
            'retry_after_seconds':COOLDOWN,
            'hint':'本次网络连接失败，已自动跳过并保留配置；先发现并查询其他来源。60 秒后自动重试，切换网络后可用 research_setup(action="network_reset") 立即清除等待。不会自行切换代理或要求注册。'}


def skip_result(entry, info):
    return {'ok':False,'command':entry['command'],'error':'network_unavailable',
            'skipped':True,'skip_reason':'recent_network_failure',
            'retry_after_seconds':max(0,int(info['retry_at']-time.time())),
            'diagnostics':{'previous_error':info['reason']},
            'hint':'已根据刚才的真实连接失败跳过此命令；请先用其他来源。稍后自动恢复，或在网络变化后调用 research_setup(action="network_reset")。'}
