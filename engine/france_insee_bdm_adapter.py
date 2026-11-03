"""French INSEE BDM SDMX public series by IDBANK."""
import release_runtime
import argparse, json, re, xml.etree.ElementTree as ET
import requests
ROOT = 'https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/'

def series(ids, latest=12, metadata_only=False):
    if not isinstance(ids, str) or not re.fullmatch('[0-9]{9}(?:\\+[0-9]{9}){0,4}', ids):
        raise ValueError('provide 1–5 nine-digit IDBANKs separated by +')
    if isinstance(latest, bool) or not isinstance(latest, int) or (not 1 <= latest <= 100):
        raise ValueError('latest must be an integer 1–100')
    if not isinstance(metadata_only, bool):
        raise ValueError('metadata_only must be boolean')
    params = {'detail': 'nodata'} if metadata_only else {'lastNObservations': latest}
    with requests.get(ROOT + ids, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for x in r.iter_content(65536):
            n += len(x)
            if n > 5 * 1024 * 1024:
                raise ValueError('response exceeds 5 MiB')
            parts.append(x)
        source = r.url
    root = ET.fromstring(b''.join(parts))
    out = []
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1] == 'Series':
            out.append({'attributes': dict(node.attrib), 'observations': [dict(x.attrib) for x in node if x.tag.rsplit('}', 1)[-1] == 'Obs']})
    if not out:
        raise ValueError('no series found; check IDBANK and availability')
    return {'source': source, 'series': out, 'note': 'Values, status, unit and scale codes are raw INSEE SDMX. Consult series definition and code lists.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('ids')
    p.add_argument('--latest', type=int, default=12)
    p.add_argument('--metadata-only', action='store_true')
    a = p.parse_args()
    print(json.dumps(series(a.ids, a.latest, a.metadata_only), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
