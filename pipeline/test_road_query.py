import requests
import json
import urllib3
urllib3.disable_warnings()

# Bounding box around Bhadrachalam (+- 0.15 deg ~ 16 km)
minx, miny, maxx, maxy = 80.75, 17.55, 81.00, 17.75
bbox_str = f"{minx},{miny},{maxx},{maxy}"

base_road_url = 'https://tgrac.telangana.gov.in/arcgis/rest/services/RnB_Folder/RnB_Roads/MapServer'

for layer_id, layer_name in [(1, 'National Highway'), (3, 'State Highway'), (4, 'Major District Road'), (5, 'Other District Road')]:
    url = f"{base_road_url}/{layer_id}/query"
    params = {
        'geometry': bbox_str,
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'outFields': 'OBJECTID,Road_Name,Road_ID,Classification,Dist_Name,Mandal_Nam,Shape_Length,Length_km,Road_Surface',
        'outSR': '4326',
        'returnGeometry': 'true',
        'f': 'json'
    }
    r = requests.get(url, params=params, verify=False, timeout=15)
    data = r.json()
    feats = data.get('features', [])
    print(f"\n=== {layer_name} (Layer {layer_id}) near Bhadrachalam: {len(feats)} features ===")
    for f in feats[:5]:
        a = f['attributes']
        geom = f['geometry']
        paths = geom.get('paths', [])
        total_pts = sum(len(p) for p in paths)
        print(f"  ID={a.get('OBJECTID')} Road={a.get('Road_ID')}: {a.get('Road_Name')} (Mandal: {a.get('Mandal_Nam')}, {a.get('Dist_Name')}, Surface: {a.get('Road_Surface')}, Length: {a.get('Length_km'):.2f}km, Pts: {total_pts})")
