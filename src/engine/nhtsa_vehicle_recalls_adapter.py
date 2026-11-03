"""NHTSA public vehicle model and recall API, no VIN lookup."""
import release_runtime
import requests
BASE = 'https://api.nhtsa.gov'

def _get(path, params):
    response = requests.get(BASE + path, params=params, timeout=30, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or 'results' not in data:
        raise ValueError('Unexpected NHTSA response')
    return data

def _year(year):
    if isinstance(year, bool) or not str(year).isdigit() or len(str(year)) != 4:
        raise ValueError('model_year must be a four-digit year')
    return str(year)

def _name(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be nonempty')
    return value.strip()

def makes(model_year):
    return _get('/products/vehicle/makes', {'modelYear': _year(model_year), 'issueType': 'r'})

def models(model_year, make):
    return _get('/products/vehicle/models', {'modelYear': _year(model_year), 'make': _name(make, 'make'), 'issueType': 'r'})

def recalls(model_year, make, model):
    return _get('/recalls/recallsByVehicle', {'modelYear': _year(model_year), 'make': _name(make, 'make'), 'model': _name(model, 'model')})
