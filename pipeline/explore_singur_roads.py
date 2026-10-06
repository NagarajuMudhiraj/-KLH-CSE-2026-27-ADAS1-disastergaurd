import requests
import json
import urllib3
urllib3.disable_warnings()

# Singur Dam: 17.75, 77.9283 (+- 0.15 deg)
bbox_singur = "77.80,17.65,78.05,17.85"
base_road_url = 'https://tgrac.telangana.gov.in/arcgis/rest/services/RnB_Folder/RnB_Roads/MapServer'

for lid, lname in [(1, 'NH'), (3, 'SH'), (4, 'MDR'), (5, 'ODR')]:
    r = requests.get(f"{base_road_url}/{lid}/query", params={
        'geometry': bbox_singur, 'geometryType': 'esriGeometryEnvelope', 'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326', 'outFields': 'OBJECTID,Road_Name,Road_ID,Classification,Dist_Name,Mandal_Nam,Shape_Length,Length_km,Road_Surface',
        'outSR': '4326', 'returnGeometry': 'true', 'f': 'json'
    }, verify=False, timeout=15)
    feats = r.json().get('features', [])
    print(f"{lname} near Singur: {len(feats)} features")
    for f in feats[:3]:
        a = f['attributes']
        lkm = a.get('Length_km') or 0.0
        print(f"  {a.get('Road_ID')}: {a.get('Road_Name')} ({a.get('Dist_Name')}, {lkm:.2f} km)")
