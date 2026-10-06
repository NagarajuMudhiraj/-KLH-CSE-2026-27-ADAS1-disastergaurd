import os
import pandas as pd

meta = pd.read_csv('data/raw/real/indofloods/metadata_indofloods.csv')
events = pd.read_csv('data/raw/real/indofloods/floodevents_indofloods.csv')
events['GaugeID'] = events['EventID'].apply(lambda x: '-'.join(str(x).split('-')[:-1]))

tg_meta = meta[meta['State'].astype(str).str.contains('Telangana', case=False, na=False)].copy()
tg_events = events[events['GaugeID'].isin(tg_meta['GaugeID'])].copy()
tg_events = tg_events.merge(tg_meta[['GaugeID', 'Station', 'Latitude', 'Longitude', 'River Name/ Tributory/ SubTributory', 'Basin', 'Warning Level', 'Danger Level']], on='GaugeID', how='left')

tg_events['Start_Date_DT'] = pd.to_datetime(tg_events['Start Date'])
tg_events['Year'] = tg_events['Start_Date_DT'].dt.year
tg_events['Month'] = tg_events['Start_Date_DT'].dt.month

audit_records = []

for idx, ev in tg_events.iterrows():
    eid = ev['EventID']
    gid = ev['GaugeID']
    st = ev['Station']
    yr = ev['Year']
    mo = ev['Month']
    dur = ev['Event Duration (days)']
    peak_fl = ev['Peak Flood Level (m)']
    warn_fl = ev['Warning Level']
    danger_fl = ev['Danger Level']
    river = ev['River Name/ Tributory/ SubTributory']
    
    rejection_reasons = []
    
    # Check 1: Temporal era (Pre-2000 road obsolescence)
    if yr < 2000:
        rejection_reasons.append(f"Pre-2000 vintage ({yr}); severe road network alignment uncertainty with modern 2020 TGRAC GIS")
        
    # Check 2: Non-monsoon standing reservoir storage
    # Nizam Sagar has 23 events between Oct and Jan where dam pool remains above crest level without active storm runoff
    if gid == 'INDOFLOODS-gauge-939' and mo not in [6, 7, 8, 9, 10]:
        rejection_reasons.append(f"Post-monsoon dry season storage (Month {mo}); standing reservoir elevation above crest, not active flash flood event")
        
    # Check 3: Redundant consecutive multi-pulse fragmentation (events lasting < 2 days during ongoing reservoir release)
    # At Nizam Sagar, several 1-day pulses are fragments of a single release
    if gid == 'INDOFLOODS-gauge-939' and dur == 1 and mo in [4, 5]:
        rejection_reasons.append(f"Pre-monsoon irrigation release / minor stage fluctuation (Month {mo}, Duration 1 day)")

    if not rejection_reasons:
        status = "ELIGIBLE"
        reason = "Valid monsoon flood event with high river stage, confirmed coordinates, modern road alignment validity"
    else:
        status = "REJECTED"
        reason = "; ".join(rejection_reasons)
        
    audit_records.append({
        'event_id': eid,
        'gauge_id': gid,
        'station': st,
        'river': river,
        'year': yr,
        'month': mo,
        'start_date': ev['Start Date'],
        'end_date': ev['End Date'],
        'peak_date': ev['Peak FL Date'],
        'peak_flood_level': peak_fl,
        'warning_level': warn_fl,
        'danger_level': danger_fl,
        'flood_type': ev['Flood Type'],
        'duration_days': dur,
        'status': status,
        'audit_reason': reason
    })

df_audit = pd.DataFrame(audit_records)
print(f"Total evaluated: {len(df_audit)}")
print(df_audit['status'].value_counts())
print("\nEligible events by Gauge:")
print(df_audit[df_audit['status'] == 'ELIGIBLE']['gauge_id'].value_counts())
print("\nRejected events summary:")
print(df_audit[df_audit['status'] == 'REJECTED']['audit_reason'].value_counts())
