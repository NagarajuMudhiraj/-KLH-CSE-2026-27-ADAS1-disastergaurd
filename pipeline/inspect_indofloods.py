import os
import zipfile
import pandas as pd

indofloods_dir = r'data\raw\real\indofloods'
meta = pd.read_csv(os.path.join(indofloods_dir, 'metadata_indofloods.csv'))
events = pd.read_csv(os.path.join(indofloods_dir, 'floodevents_indofloods.csv'))
precip = pd.read_csv(os.path.join(indofloods_dir, 'precipitation_variables_indofloods.csv'))
catch = pd.read_csv(os.path.join(indofloods_dir, 'catchment_characteristics_indofloods.csv'))

print('=== METADATA SUMMARY ===')
print('Columns:', meta.columns.tolist())
print('Total gauges:', len(meta))
print('Unique states:\n', meta['State'].value_counts(dropna=False))

# Check how EventID maps to GaugeID
print('\n=== EVENT SUMMARY ===')
print('Columns:', events.columns.tolist())
print('Total events:', len(events))
print('Sample EventIDs:', events['EventID'].head().tolist())

# EventID like INDOFLOODS-gauge-1010-1 -> gauge is INDOFLOODS-gauge-1010
events['GaugeID'] = events['EventID'].apply(lambda x: '-'.join(str(x).split('-')[:-1]))
matched_gauges = set(events['GaugeID']).intersection(set(meta['GaugeID']))
print(f"Gauges in events: {events['GaugeID'].nunique()}, matched with metadata: {len(matched_gauges)}")

# Check Telangana in metadata
tg_gauges = meta[meta['State'].astype(str).str.contains('Telangana', case=False, na=False)]
print('\n=== TELANGANA GAUGES DETAILS ===')
for idx, row in tg_gauges.iterrows():
    print(f"{row['GaugeID']}: Station='{row['Station']}', Lat={row['Latitude']}, Lon={row['Longitude']}, River='{row['River Name/ Tributory/ SubTributory']}', WarningLvl={row['Warning Level']}, DangerLvl={row['Danger Level']}")

tg_events = events[events['GaugeID'].isin(tg_gauges['GaugeID'])]
print(f'\nTotal events matching Telangana gauges: {len(tg_events)}')
if len(tg_events) > 0:
    print(tg_events[['EventID', 'Start Date', 'End Date', 'Peak Flood Level (m)', 'Peak FL Date', 'Event Duration (days)', 'Flood Type']].head(15))

# Also check Andhra Pradesh or nearby Krishna/Godavari basin gauges
kg_gauges = meta[meta['Basin'].astype(str).str.contains('Krishna|Godavari', case=False, na=False)]
print(f'\nTotal Krishna/Godavari basin gauges: {len(kg_gauges)}')
print(kg_gauges[['GaugeID', 'Station', 'Latitude', 'Longitude', 'State', 'Basin']].head(10))

# Check zipfile contents
zip_path = os.path.join(indofloods_dir, 'catchments_shapefiles_indofloods.zip')
with zipfile.ZipFile(zip_path, 'r') as z:
    names = z.namelist()
    print(f'\n=== SHAPEFILES ZIP ===')
    print(f'Total files in zip: {len(names)}')
    print('Sample files:', names[:15])
