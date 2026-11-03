"""CORDIS Horizon Europe projects from official public bulk CSV ZIP."""
import release_runtime
import argparse, csv, io, json, tempfile, zipfile
import requests
URL = 'https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip'
LANDING = 'https://data.europa.eu/data/datasets/cordis-eu-research-projects-under-horizon-europe-2021-2027'

def search(keyword, limit=20):
    if not keyword or len(keyword) > 150 or (not 1 <= limit <= 50):
        raise ValueError('invalid keyword or limit')
    with tempfile.TemporaryFile() as f:
        with requests.get(URL, timeout=(15, 100), stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
            r.raise_for_status()
            totalbytes = 0
            for b in r.iter_content(131072):
                totalbytes += len(b)
                if totalbytes > 70 * 1024 * 1024:
                    raise ValueError('download exceeds 70 MiB')
                f.write(b)
        f.seek(0)
        with zipfile.ZipFile(f) as z:
            info = z.getinfo('project.csv')
            if info.file_size > 150 * 1024 * 1024:
                raise ValueError('project CSV exceeds 150 MiB')
            with z.open(info) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as stream:
                reader = csv.DictReader(stream, delimiter=';')
                required = {'id', 'title', 'acronym', 'objective', 'keywords'}
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError('unexpected project CSV schema')
                hits = []
                count = 0
                needle = keyword.casefold()
                for row in reader:
                    if not any((needle in (row.get(k) or '').casefold() for k in ('title', 'acronym', 'objective', 'keywords'))):
                        continue
                    count += 1
                    if len(hits) < limit:
                        hits.append(row)
    return {'source': URL, 'metadata': LANDING, 'download_bytes': totalbytes, 'matched': count, 'results': hits, 'note': 'CORDIS bulk snapshot. Monetary CSV fields use decimal comma. See source documentation and contentUpdateDate.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
