import math
import heapq
import time
from typing import List, Dict, Any, Tuple, Optional

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate Haversine distance in kilometers between two coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def point_to_segment_distance_km(p1: Tuple[float, float], p2: Tuple[float, float], pt: Tuple[float, float]) -> float:
    """
    Calculate the exact minimum distance in kilometers from a hazard point (pt)
    to a road segment (p1 -> p2) using local equirectangular projection.
    """
    lat1, lng1 = p1
    lat2, lng2 = p2
    plat, plng = pt

    cos_lat = math.cos(math.radians((lat1 + lat2) / 2.0))
    x1, y1 = 0.0, 0.0
    x2 = (lng2 - lng1) * 111.32 * cos_lat
    y2 = (lat2 - lat1) * 110.574

    px = (plng - lng1) * 111.32 * cos_lat
    py = (plat - lat1) * 110.574

    dx = x2 - x1
    dy = y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq <= 1e-9:
        return math.sqrt(px * px + py * py)

    t = max(0.0, min(1.0, (px * dx + py * dy) / seg_len_sq))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

class ModifiedDijkstraRouting:
    """
    Risk-Weighted Modified Dijkstra Algorithm for Autonomous Disaster-Aware Navigation.
    Evaluates origin, destination, disaster risk zones (Green/Yellow/Red/Purple) and active hazards.
    Instantly and autonomously shifts navigation to safe bypass corridors whenever any hazard compromises the route.
    """

    RISK_LEVEL_WEIGHTS = {
        "Green": 1.1,
        "Yellow": 2.5,
        "Red": 12.0,
        "Purple": 35.0,
        "Critical": 35.0,
        "High": 12.0,
        "Medium": 2.5,
        "Low": 1.1
    }

    HAZARD_TYPE_WEIGHTS = {
        "Flood": 15.0,
        "Fire": 25.0,
        "Landslide": 20.0,
        "Earthquake": 20.0,
        "Road Blocked": 30.0,
        "Accident": 8.0,
        "Heavy Traffic": 3.0,
        "Normal": 1.0
    }

    def __init__(self, influence_radius_km: float = 3.0):
        self.influence_radius_km = influence_radius_km

    def calculate_segment_cost(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        disaster_zones: List[Dict[str, Any]],
        hazards: List[Dict[str, Any]]
    ) -> Tuple[float, float, List[Dict[str, Any]]]:
        """
        Calculates traversing cost for road edge (p1 -> p2).
        Returns (weighted_cost, physical_distance_km, encountered_risks).
        """
        dist_km = haversine_km(p1[0], p1[1], p2[0], p2[1])
        if dist_km <= 0:
            return 0.0, 0.0, []

        multiplier = 1.0
        encountered = []

        # 1. Check Disaster Risk Zones (Green, Yellow, Red, Purple)
        for zone in disaster_zones:
            z_lat = zone.get("lat") or (zone.get("location", {}).get("lat") if isinstance(zone.get("location"), dict) else 0.0) or 0.0
            z_lng = zone.get("lng") or (zone.get("location", {}).get("lng") if isinstance(zone.get("location"), dict) else 0.0) or 0.0
            if not z_lat or not z_lng:
                continue

            z_radius_km = (float(zone.get("radius_meters", 1200)) / 1000.0) or 1.2
            z_risk = zone.get("risk_level", "Medium")

            d_to_zone = point_to_segment_distance_km(p1, p2, (z_lat, z_lng))
            if d_to_zone <= z_radius_km:
                decay = max(0.2, 1.0 - (d_to_zone / z_radius_km))
                risk_weight = self.RISK_LEVEL_WEIGHTS.get(z_risk, 3.0)
                added_penalty = (risk_weight - 1.0) * decay * 4.0
                multiplier += added_penalty

                encountered.append({
                    "name": zone.get("name", "Disaster Zone"),
                    "risk_level": z_risk,
                    "distance_km": round(d_to_zone, 2),
                    "penalty": round(added_penalty, 2)
                })

        # 2. Check Active Hazards (Fire, Flood, Landslide, Accidents, Roadblocks)
        for h in hazards:
            if h.get("status", "Active") == "Resolved":
                continue

            h_lat = h.get("lat") or (h.get("location", {}).get("lat") if isinstance(h.get("location"), dict) else 0.0) or 0.0
            h_lng = h.get("lng") or (h.get("location", {}).get("lng") if isinstance(h.get("location"), dict) else 0.0) or 0.0
            if not h_lat or not h_lng:
                continue

            h_type = h.get("disasterType") or h.get("type") or "Hazard"
            h_sev = str(h.get("severity", "Medium")).title()
            h_score = float(h.get("riskScore", 0.0) or 0.0)

            d_to_h = point_to_segment_distance_km(p1, p2, (h_lat, h_lng))
            if d_to_h <= self.influence_radius_km:
                decay = max(0.25, 1.0 - (d_to_h / self.influence_radius_km))
                base_weight = self.HAZARD_TYPE_WEIGHTS.get(h_type, 10.0)

                if h_sev in ["Critical", "High"]:
                    base_weight *= 2.5
                elif h_sev == "Medium":
                    base_weight *= 1.5

                if h_score > 0:
                    base_weight += (h_score / 4.0)

                added_penalty = base_weight * decay
                multiplier += added_penalty

                encountered.append({
                    "type": h_type,
                    "severity": h_sev,
                    "risk_score": h_score,
                    "distance_km": round(d_to_h, 2),
                    "penalty": round(added_penalty, 2)
                })

        weighted_cost = dist_km * multiplier
        return weighted_cost, dist_km, encountered

    def _solve_corridor(
        self,
        origin: Tuple[float, float],
        dest: Tuple[float, float],
        disaster_zones: List[Dict[str, Any]],
        hazards: List[Dict[str, Any]],
        detour_bias: float
    ) -> Dict[str, Any]:
        """Solves Dijkstra pathfinding for a spatial arc corridor."""
        num_steps = 14
        waypoints = [origin]

        dlat = dest[0] - origin[0]
        dlng = dest[1] - origin[1]
        norm = math.sqrt(dlat**2 + dlng**2) or 1.0
        perp_lat = -dlng / norm * detour_bias
        perp_lng =  dlat / norm * detour_bias

        for i in range(1, num_steps):
            t = i / float(num_steps)
            w_lat = origin[0] + dlat * t
            w_lng = origin[1] + dlng * t

            offset = math.sin(t * math.pi)
            w_lat += perp_lat * offset
            w_lng += perp_lng * offset

            waypoints.append((round(w_lat, 5), round(w_lng, 5)))
        waypoints.append(dest)

        n = len(waypoints)
        adj: Dict[int, List[Tuple[int, float, float, List[Dict[str, Any]]]]] = {i: [] for i in range(n)}

        for i in range(n):
            for j in range(i + 1, min(i + 3, n)):
                cost, phys_d, enc = self.calculate_segment_cost(waypoints[i], waypoints[j], disaster_zones, hazards)
                adj[i].append((j, cost, phys_d, enc))

        dist = {i: float('inf') for i in range(n)}
        dist[0] = 0.0
        parent = {i: -1 for i in range(n)}
        pq = [(0.0, 0)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            if u == n - 1:
                break

            for v, weight, phys_d, enc in adj[u]:
                if dist[u] + weight < dist[v]:
                    dist[v] = dist[u] + weight
                    parent[v] = u
                    heapq.heappush(pq, (dist[v], v))

        path_idx = []
        curr = n - 1
        while curr != -1:
            path_idx.append(curr)
            curr = parent[curr]
        path_idx.reverse()

        if len(path_idx) <= 1:
            path_idx = list(range(n))

        final_waypoints = [[waypoints[i][0], waypoints[i][1]] for i in path_idx]
        total_phys_distance = sum(
            haversine_km(final_waypoints[i][0], final_waypoints[i][1], final_waypoints[i+1][0], final_waypoints[i+1][1])
            for i in range(len(final_waypoints) - 1)
        )
        total_phys_distance = round(total_phys_distance, 2)
        est_time_min = round((total_phys_distance / 42.0) * 60.0, 1)

        # Collect exact encountered risks along the chosen route
        final_encountered = []
        seen_keys = set()
        for k in range(len(path_idx) - 1):
            u_idx = path_idx[k]
            v_idx = path_idx[k+1]
            _, _, seg_enc = self.calculate_segment_cost(waypoints[u_idx], waypoints[v_idx], disaster_zones, hazards)
            for item in seg_enc:
                key = f"{item.get('type') or item.get('name')}_{item.get('distance_km')}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    final_encountered.append(item)

        penalty_sum = sum(e.get("penalty", 0.0) for e in final_encountered)
        if len(final_encountered) == 0:
            safety_score = 100
        else:
            safety_score = max(0, min(95, int(100 - (penalty_sum * 4.5))))

        risk_level = (
            "Low Risk (Green)" if safety_score >= 85 else
            "Medium Risk (Yellow)" if safety_score >= 60 else
            "High Risk (Red)" if safety_score >= 35 else
            "Critical Risk (Purple)"
        )

        cost_val = 9999.0 if math.isinf(dist[n - 1]) else round(dist[n - 1], 2)

        return {
            "waypoints": final_waypoints,
            "distance_km": total_phys_distance,
            "duration_min": est_time_min,
            "weighted_cost": cost_val,
            "safety_score": safety_score,
            "risk_level": risk_level,
            "encountered": final_encountered,
            "penalty_sum": penalty_sum,
            "detour_bias": detour_bias
        }

    def run_modified_dijkstra(
        self,
        origin: Tuple[float, float],
        dest: Tuple[float, float],
        disaster_zones: List[Dict[str, Any]],
        hazards: List[Dict[str, Any]],
        detour_bias: float = 0.0
    ) -> Dict[str, Any]:
        """
        Executes Multi-Corridor Disaster Dijkstra.
        Evaluates direct path and lateral bypass corridors.
        Automatically triggers autonomous rerouting if direct corridor has high risk or hazards.
        """
        t0 = time.time()

        # 1. Evaluate Direct Corridor (detour_bias = 0.0)
        direct_result = self._solve_corridor(origin, dest, disaster_zones, hazards, detour_bias=0.0)

        # 2. Check if direct corridor encounters any hazards or critical zones
        has_critical_hazard = any(
            e.get("severity") in ["Critical", "High"] or
            e.get("risk_level") in ["Purple", "Red"] or
            e.get("penalty", 0) > 2.0 or
            str(e.get("type", "")).lower() in ["fire", "flood", "road blocked", "landslide", "earthquake"]
            for e in direct_result["encountered"]
        )

        is_compromised = (
            len(direct_result["encountered"]) > 0 or
            direct_result["safety_score"] < 88 or
            direct_result["penalty_sum"] > 0.4 or
            has_critical_hazard
        )

        # 3. Evaluate lateral bypass alternatives (+/- lateral curves)
        candidate_biases = [0.035, -0.035, 0.065, -0.065, 0.095, -0.095]
        evaluated_bypasses = []

        for bias in candidate_biases:
            candidate = self._solve_corridor(origin, dest, disaster_zones, hazards, detour_bias=bias)
            evaluated_bypasses.append(candidate)

        # Sort bypasses prioritizing Safety Score, then fewest hazards, lowest penalty, shortest distance
        evaluated_bypasses.sort(
            key=lambda c: (
                c["safety_score"],
                -len(c["encountered"]),
                -c["penalty_sum"],
                -c["distance_km"]
            ),
            reverse=True
        )

        best_bypass = evaluated_bypasses[0] if evaluated_bypasses else None

        # 4. Autonomous Rerouting Decision:
        # If primary corridor is compromised and a safe bypass exists, reroute immediately!
        if is_compromised and best_bypass:
            selected = best_bypass
            is_rerouted = True
            first_hazard = direct_result["encountered"][0] if direct_result["encountered"] else {}
            hazard_type = first_hazard.get("type") or first_hazard.get("name") or "Severe Road Hazard"
            hazard_sev = first_hazard.get("severity") or first_hazard.get("risk_level") or "High"
            hazard_dist = first_hazard.get("distance_km", 0.5)

            detour_reason = (
                f"AUTONOMOUS REROUTE: {hazard_type} ({hazard_sev}) detected {hazard_dist}km ahead on primary route. "
                f"Navigation automatically diverted to Safe Bypass Corridor (Safety Score: {best_bypass['safety_score']}%)."
            )
        else:
            selected = direct_result
            is_rerouted = False
            detour_reason = "Direct corridor is clear and safe for travel."

        elapsed_ms = round((time.time() - t0) * 1000, 2)

        return {
            "route_id": "modified_dijkstra_safe",
            "algorithm": "Modified Dijkstra Dynamic Rerouting Engine",
            "waypoints": selected["waypoints"],
            "distance_km": selected["distance_km"],
            "duration_min": selected["duration_min"],
            "weighted_cost": selected["weighted_cost"],
            "safety_score": selected["safety_score"],
            "risk_level": selected["risk_level"],
            "encountered_risks_count": len(selected["encountered"]),
            "is_rerouted": is_rerouted,
            "detour_reason": detour_reason,
            "compromised_waypoints": direct_result["waypoints"] if is_rerouted else None,
            "intercepted_hazards": direct_result["encountered"] if is_rerouted else [],
            "computation_ms": elapsed_ms
        }

dijkstra_engine = ModifiedDijkstraRouting()
