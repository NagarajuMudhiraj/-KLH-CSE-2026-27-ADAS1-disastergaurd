import requests
import json
import urllib3
urllib3.disable_warnings()

base_url = 'https://tgrac.telangana.gov.in/arcgis/rest/services'

def get_layer_details(service_path, layer_id):
    url = f"{base_url}/{service_path}/MapServer/{layer_id}?f=pjson"
    r = requests.get(url, verify=False, timeout=15)
    if r.status_code != 200:
        print(f"Failed {url}: {r.status_code}")
        return None
    data = r.json()
    print(f"\n=======================================================")
    print(f"Layer: {service_path} / [{layer_id}] {data.get('name')}")
    print(f"Type: {data.get('type')}, Geometry: {data.get('geometryType')}")
    print(f"Capabilities: {data.get('capabilities')}")
    print(f"Supports Statistics: {data.get('supportsStatistics')}")
    print(f"Supports Advanced Queries: {data.get('supportsAdvancedQueries')}")
    print(f"Time Info: {data.get('timeInfo')}")
    print(f"Spatial Reference: {data.get('extent', {}).get('spatialReference')}")
    print("Fields:")
    for f in data.get('fields', []):
        print(f"  - {f.get('name')} ({f.get('type')}, alias='{f.get('alias')}')")
    
    # Try querying 3 sample features
    q_url = f"{base_url}/{service_path}/MapServer/{layer_id}/query"
    params = {
        'where': '1=1',
        'outFields': '*',
        'returnGeometry': 'true',
        'resultRecordCount': 3,
        'f': 'json'
    }
    qr = requests.get(q_url, params=params, verify=False, timeout=15)
    if qr.status_code == 200:
        qdata = qr.json()
        features = qdata.get('features', [])
        print(f"Query sample features returned: {len(features)}")
        if features:
            print("Sample feature attributes:")
            for feat in features[:2]:
                print(" ", feat.get('attributes'))
                geom = feat.get('geometry', {})
                geom_keys = list(geom.keys())
                print("  Geometry summary:", geom_keys)
    else:
        print(f"Query failed with status: {qr.status_code}")

layers_to_test = [
    ('GHMCNalas_Folder/GHMCNalas_vul', 1),   # Inundation Areas
    ('GHMCNalas_Folder/GHMCNalas_vul', 2),   # Nala
    ('GHMCNalas_Folder/GHMCNalas_vul', 10),  # OUTER_RINGROAD_BND_ROADS
    ('RnB_Folder/RnB_Roads', 1),             # National Highway
    ('RnB_Folder/RnB_Roads', 3),             # State Highway
    ('RnB_Folder/RnB_Roads', 4),             # District Major Road
    ('RnB_Folder/RnB_Roads', 5),             # Other District Road
]

for spath, lid in layers_to_test:
    get_layer_details(spath, lid)
