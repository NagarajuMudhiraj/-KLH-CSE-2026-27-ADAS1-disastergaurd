import requests
import json
import urllib3
urllib3.disable_warnings()

base_url = 'https://tgrac.telangana.gov.in/arcgis/rest/services'

def get_json(url):
    try:
        r = requests.get(url + '?f=pjson', verify=False, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

svcs = [
    'HMDA_Folder/HMDA',
    'GHMCDockets_Folder/GHMC_Dockets',
    'GHMCNalas_Folder/GHMCNalas_vul',
    'RnB_Folder/RnB_Roads'
]

for svc in svcs:
    sdata = get_json(f"{base_url}/{svc}/MapServer")
    if not sdata:
        continue
    print(f"\n======================================")
    print(f"Service: {svc}")
    print(f"Description: {sdata.get('serviceDescription', '')[:100]}")
    print(f"Spatial Reference: {sdata.get('spatialReference')}")
    print(f"Initial Extent: {sdata.get('initialExtent')}")
    print(f"Full Extent: {sdata.get('fullExtent')}")
    layers = sdata.get('layers', [])
    print(f"Layers ({len(layers)}):")
    for l in layers:
        lid = l.get('id')
        lname = l.get('name')
        sub = l.get('subLayerIds')
        print(f"  [{lid}] {lname} (subLayers: {sub})")
