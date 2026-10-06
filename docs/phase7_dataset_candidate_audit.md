# Phase 7 Real-World Tabular Dataset Candidate Audit

## Repository result

The repository contains CSV, JSON/JSONL, and Parquet road-risk files, but none
is eligible: V2 has live-2026 weather and defaults; V3 has generated per-row
coordinates/times and hardcoded geography/traffic; V4 is the intentional empty
provenance gate. There is no standalone road-closure, traffic, weather+road,
or database export with source-native road observations.

## External candidates

| Candidate | Source / licence | Identity, geography and time | Native target and independence | Features / inference compatibility | Decision |
|---|---|---|---|---|
| Australia National Roadworks and Road Closures (NFDH) | [NFDH](https://datahub.roadsafety.gov.au/infrastructure/roadworks-and-road-closures); licence not verified in this audit | Australia; state/territory feeds; historical database | Closure/condition categories are harmonised and sometimes categorised by ingest logic | Roadworks/closure evidence; no verified row extract or historical weather/traffic join inspected | REJECT: target can be derived by the aggregator; row schema/access and feature-time joins unverified |
| DriveBC Open511 | [BC Open Government](https://open.canada.ca/data/dataset/23a839e3-8fb4-4569-bb3d-c28a7621f687); Open Government Licence–BC | British Columbia, Canada; Open511 geospatial events | Official road event, closure, weather, and work status | Live API; possible future provider | REJECT: described as real-time, not a verified historical training extract |
| WA WebEOC road incidents | [WA catalogue](https://catalogue.data.wa.gov.au/en/dataset/mrwa-webeoc-road-incidents); CC BY 4.0 | Western Australia; current road map incidents | Closure type includes closed/open-with-caution/open-with-conditions; incident type includes flooding | GIS service; target has useful native semantics | REJECT: source describes the most recent incidents, not historical observations |
| Victoria Unplanned Disruptions v3 | [Transport Victoria](https://opendata.transport.vic.gov.au/dataset/unplanned-disruptions-road/resource/1b185c7f-d4b2-404d-a65c-b5a80da7582d); CC BY 4.0 | Victoria, Australia; WGS84 API | `Road closed`, `Lanes closed`, `Changed conditions`, `No blockage`; official operational feed | Location/reason/lanes; current/near-real-time API, `endTime` is expected/next-update time | REJECT: no verified historical archive; target changes and future expected time cannot become a feature |
| ACT historical road-closure feature layer | [ACT FeatureServer](https://services1.arcgis.com/E5n4f1VY84i0xSjy/arcgis/rest/services/Road_Closures_public_view_HISTORICAL/FeatureServer/0/); licence not stated in inspected schema | ACT, Australia; start/end and approval timestamps, road names/reason | Official proposed/approved road closures | Layer metadata indicates no geometry properties; no source-native coordinates available in verified schema | REJECT: cannot meet spatial contract; planned closures also differ from observed road state |
| Ottawa Historical Emergency Road Closures 2019 | [Ottawa catalogue](https://data.urbandatacentre.ca/en/catalogue/open-ottawa-9de005-historical-emergency-road-closure-locations-2019); Ottawa Open Data Licence v2.0 | Ottawa, Canada; local entered/ended timestamps and marker latitude/longitude | Staff-recorded closure/impact message | Historic CSV is advertised; labels can map only explicit closures to BLOCKED | HOLD, not selected: 2019 archive has not been downloaded/row-validated; staff note it is not comprehensive and active-map times may differ from actual event duration. It supplies no SAFE/RISKY class or feature join. |
| 2017 flooded roads closed ArcGIS layer | [FeatureServer](https://services2.arcgis.com/jWXb6JPWtBjOCalT/ArcGIS/rest/services/2017_may_flooded_roads_closed/FeatureServer/0); licence unverified | US 2017 flood event; time-enabled UTC layer with road-line attributes | Flooded-road closure context | `FLOOD_COND`, depth, road description, start/end fields appear in schema | HOLD, not selected: public schema is visible but no downloadable row extract, geometry precision, label definition, or independent feature join was verified. Do not infer label from `FLOOD_COND`. |
| xBD/xView2 | [xBD-S12 metadata](https://github.com/prs-eth/xbd-s12/blob/main/DATASET.md); source licence must be checked before use | Multiple global disaster events with patch geometry/time metadata | Building damage classes, not road condition | Satellite imagery/metadata only | REJECT: mapping building damage to ADAS road classes would fabricate labels |

## Source semantics and mapping rules

Only a direct, official closure state could map `ROAD_CLOSED` to ADAS
`BLOCKED (2)`, preserving `original_label=ROAD_CLOSED` and
`mapped_label=BLOCKED`. `Open with caution` is not automatically RISKY, and
missing a closure is not SAFE. No mapping was performed in V5.

## What would make a candidate eligible

1. Downloadable/API row extract with a stable identifier, observation/activation
   time, location geometry/coordinates, and source licence.
2. Independent observed road-status label with definition and source timestamp.
3. A documented historical weather/road join keyed to the actual location and
   time; no retrieval-time substitution.
4. At least one compatible feature obtainable at ADAS inference time. The
   current production traffic adapter is a stub, so traffic remains excluded.
5. Independent event/geography partitions and enough source-semantic class
   coverage. No synthetic SAFE/RISKY examples may balance closure data.
