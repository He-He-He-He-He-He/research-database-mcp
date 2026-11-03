"""WTO Trade Facilitation Agreement transparency information."""
import release_runtime
import json, re, subprocess
import requests
URL = 'https://api.wto.org/tfad/transparency/procedures_contacts_single_window'

def countries(codes):
    if not isinstance(codes, str) or not re.fullmatch('\\d{3}(?:,\\d{3}){0,19}', codes):
        raise ValueError('Specify 1–20 ISO numeric country codes, each 3 digits')
    p = release_runtime.run(['security', 'find-generic-password', '-s', 'research-toolkit-wto-standard', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=15)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('WTO Keychain credential unavailable')
    params = [('countries[]', x) for x in codes.split(',')]
    try:
        with requests.get(URL, params=params, headers={'Ocp-Apim-Subscription-Key': p.stdout.strip()}, timeout=30, stream=True, allow_redirects=False) as r:
            if r.is_redirect:
                raise RuntimeError('Unexpected WTO API redirect')
            if not r.ok:
                raise RuntimeError('WTO TFAD returned HTTP ' + str(r.status_code))
            chunks = []
            size = 0
            for c in r.iter_content(65536):
                size += len(c)
                if size > 8 * 1024 * 1024:
                    raise RuntimeError('Response exceeds 8 MiB')
                chunks.append(c)
        data = json.loads(b''.join(chunks))
    except requests.RequestException as e:
        raise RuntimeError('WTO TFAD request failed: ' + type(e).__name__) from None
    if not isinstance(data, list):
        raise RuntimeError('Unexpected WTO TFAD response')
    return {'source': 'WTO Trade Facilitation Agreement Database', 'source_info': 'https://apiportal.wto.org/api-details#api=tfad', 'countries': codes.split(','), 'items': data, 'returned': len(data), 'note': '进出口与过境程序、咨询点和单一窗口的信息；资料由成员通报，可能滞后或不完整。网站和联系方式须到发布机构核对，不是法律意见。'}
