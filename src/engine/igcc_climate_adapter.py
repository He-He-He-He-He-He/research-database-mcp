"""IGCC 2025 curated global climate series hosted by IIASA ixmp4.

Independent scientific assessment, not an official IPCC product. World-level
series include estimates, uncertainties and projections; preserve model,
scenario, unit and year. Dataset: https://doi.org/10.5281/zenodo.20600829
Paper: https://doi.org/10.5194/essd-18-3889-2026; CC BY 4.0.
"""
import release_runtime
import requests
BASE = 'https://ixmp4.ece.iiasa.ac.at/v1/igcc-2025/'

def _query(path, body):
    response = requests.patch(BASE + path, json=body, timeout=30)
    response.raise_for_status()
    return response.json()

def variables():
    """List public variable names and IDs; inspect pagination and total."""
    return _query('iamc/variables/list', {})

def observations(variable):
    """Fetch one named variable, retaining models, scenarios and units.

    The API caps a page at 10,000 observations: compare total and data length
    before assuming a result is complete.
    """
    if not isinstance(variable, str) or not variable.strip():
        raise ValueError('variable must be a nonempty exact variable name')
    return _query('iamc/datapoints/tabulate', {'variable': {'name': variable}, 'join_parameters': True, 'join_runs': True})
