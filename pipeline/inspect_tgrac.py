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

root = get_json(base_url)
folders = root.get('folders', [])

print(f"Total folders: {len(folders)}")

target_folders = [f for f in folders if any(k in f.lower() for k in [
    'rnb', 'hmda', 'ghmc', 'hydra', 'his', 'iandcad', 'musi', 'tgsrtc', 'tcur', 'watershed'
])]

all_services = []

for folder in target_folders:
    folder_url = f"{base_url}/{folder}"
    fdata = get_json(folder_url)
    if not fdata:
        continue
    services = fdata.get('services', [])
    print(f"\n=== Folder: {folder} ({len(services)} services) ===")
    for s in services:
        name = s.get('name')
        stype = s.get('type')
        print(f"  - {name} ({stype})")
        all_services.append((name, stype))

print("\n--- Inspecting specific road and flood services ---")
road_or_flood_services = [s for s in all_services if any(k in s[0].lower() for k in ['road', 'flood', 'water', 'nala', 'drain', 'inundat', 'hazard', 'hyd'])]

for name, stype in road_or_flood_services[:25]:
    svc_url = f"{base_url}/{name}/{stype}"
    sdata = get_json(svc_url)
    if not sdata:
        continue
    layers = sdata.get('layers', [])
    print(f"\nService: {name} ({stype})")
    print(f"  Description: {sdata.get('serviceDescription', '')[:100]}")
    print(f"  Layers ({len(layers)}):")
    for l in layers:
        print(f"    [{l.get('id')}] {l.get('name')} (subLayerIds: {l.get('subLayerIds')})")
