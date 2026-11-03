"""UN Population Division Data Portal: read-only public location/indicator metadata.

Data values require a token; these functions do not retrieve or generate one.
"""
import release_runtime
import json
import re
import urllib.parse
import subprocess
BASE = 'https://population.un.org/dataportalapi/api/v1/'

def _fetch(path, codes):
    if not isinstance(codes, str) or not re.fullmatch('[A-Za-z0-9,;_-]{1,120}', codes):
        raise ValueError('codes must contain only letters, digits, comma, semicolon, underscore or hyphen')
    url = BASE + path + '/' + urllib.parse.quote(codes, safe=',;_-')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], capture_output=True, text=True, check=True)
    obj = json.loads(r.stdout)
    if not isinstance(obj, list):
        raise ValueError('Unexpected UN Population metadata response')
    return obj

def locations(codes):
    """Find locations by ISO2, ISO3, or numeric UN M49 codes."""
    return _fetch('locations', codes)

def indicators(codes):
    """Find indicator metadata by IDs or documented short names."""
    return _fetch('Indicators', codes)
