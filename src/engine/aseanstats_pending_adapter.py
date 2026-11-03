"""ASEANstats official API: documented GET endpoints and raw responses."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.aseanstats.org/api/v1/'
SERVICE = 'research-toolkit-aseanstats'
ROUTES = {'social-indicators': 'metadata/social/indicators', 'population': 'social/population/data', 'education': 'social/education/data', 'health': 'social/health/data', 'macro-dimensions': 'metadata/macro/dimensions', 'gdp': 'macro/gdp', 'fdi-indicators': 'metadata/fdi/indicators', 'fdi-dimensions': 'metadata/fdi/dimensions', 'fdi': 'fdi/query', 'asean-indicators': 'basic-indicators/asean', 'member-indicators': 'basic-indicators/ams'}

def _token():
    from imap_otp_mcp.server import config
    account, _, _ = config()
    p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', account, '-w'], capture_output=True, text=True, timeout=15)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('未取得 ASEANstats 访问令牌；账号批准不等于接口已接通')
    return p.stdout.strip()

def query(kind, params=None):
    if kind not in ROUTES:
        raise ValueError('未知接口类别')
    if params is None:
        params = {}
    if not isinstance(params, dict) or len(params) > 20:
        raise ValueError('参数须为 JSON 对象，最多 20 项')
    for k, v in params.items():
        if not isinstance(k, str) or not k or len(k) > 80 or (not all((c.isascii() and (c.isalnum() or c in '_[]') for c in k))):
            raise ValueError('参数名无效')
        if not isinstance(v, (str, int, bool)) or len(str(v)) > 1000:
            raise ValueError('参数值须为短文本、整数或布尔值')
    token = _token()
    if not token or len(token) > 512 or any((c in token for c in '\r\n"\\')):
        raise RuntimeError('令牌格式无效')
    url = BASE + ROUTES[kind] + ('?' + urlencode(params) if params else '')
    try:
        proc = release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--proto', '=https', '--max-time', '35', '--max-filesize', '16000000', '--config', '-', '--write-out', '\n__STATUS__%{http_code}', url], input='header = "Authorization: Bearer ' + token + '"\nheader = "Accept: application/json"\n', capture_output=True, text=True, timeout=40)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('ASEANstats 网络请求失败') from None
    raw, sep, status = proc.stdout.rpartition('\n__STATUS__')
    if proc.returncode or not sep:
        raise RuntimeError('ASEANstats 网络请求失败')
    if status != '200':
        raise RuntimeError('ASEANstats 返回 HTTP ' + status[:3])
    if len(raw.encode('utf-8')) > 16000000:
        raise RuntimeError('响应超过 16 MB')
    try:
        data = json.loads(raw.lstrip('\ufeff'))
    except ValueError:
        raise RuntimeError('ASEANstats 未返回有效 JSON') from None
    if not isinstance(data, dict) or data.get('status') != 'success' or 'data' not in data:
        raise RuntimeError('ASEANstats 未返回预期成功响应')

    def scrub(x):
        if isinstance(x, str):
            return x.replace(token, '[redacted]')
        if isinstance(x, list):
            return [scrub(v) for v in x]
        if isinstance(x, dict):
            return {k: scrub(v) for k, v in x.items() if str(k).lower() not in ('token', 'authorization')}
        return x
    return {'source': 'ASEANstats API v1', 'endpoint': kind, 'requested_params': params, 'response': scrub(data), 'note': '保留源站返回的值、单位及分页；上游可能忽略或回退部分筛选，请逐条核对结果范围。'}
