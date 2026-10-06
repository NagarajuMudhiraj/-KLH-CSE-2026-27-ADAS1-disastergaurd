from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import RouteAnalysisInput, BatchRouteAnalysisInput
from app.database.mongodb import get_hazards_collection
from app.utils.security import get_current_user
from app.services.astar_routing import astar_engine
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter(prefix="/api/routes", tags=["Route Safety & A* Engine"])

@router.post("/analyze", response_model=None)
async def analyze_route_safety(
    input_data: RouteAnalysisInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute Disaster-Aware A* (A-Star) Pathfinding Algorithm.
    Calculates cost function:
      g(n) = Distance + Traffic + Flood_Cost + Fire_Cost + Landslide_Cost + Road_Closure_Penalty
      f(n) = g(n) + h(n) [Haversine Heuristic]
    """
    origin = (input_data.origin_lat, input_data.origin_lng)
    dest   = (input_data.destination_lat, input_data.destination_lng)

    # Fetch active hazards from MongoDB
    hazards_coll = get_hazards_collection()
    all_hazards = list(hazards_coll.find({}))
    active_hazards = [h for h in all_hazards if h.get("status", "Active") != "Resolved"]

    # Execute Disaster-Aware A* Engine
    result = astar_engine.compute_all_routes(
        origin=origin,
        dest=dest,
        hazards=active_hazards,
        is_emergency_mode=False
    )

    result["analysis_timestamp"] = datetime.utcnow().isoformat()
    return result

@router.post("/batch-analyze", response_model=None)
async def batch_analyze_routes_safety(
    input_data: BatchRouteAnalysisInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Evaluates multiple destinations using A* Engine and returns the safest & closest one.
    """
    origin = (input_data.origin_lat, input_data.origin_lng)
    
    # Fetch active hazards
    hazards_coll = get_hazards_collection()
    all_hazards = list(hazards_coll.find({}))
    active_hazards = [h for h in all_hazards if h.get("status", "Active") != "Resolved"]
    
    best_destination = None
    best_route = None
    best_score = -1
    shortest_dist = float('inf')

    # Evaluate each destination
    for dest_node in input_data.destinations:
        dest = (dest_node.lat, dest_node.lng)
        result = astar_engine.compute_all_routes(
            origin=origin,
            dest=dest,
            hazards=active_hazards,
            is_emergency_mode=True
        )
        
        # The first route is the recommended/optimal one
        optimal_route = result["routes"][0]
        
        # We want the safest score. If there's a tie, pick the shortest distance.
        score = optimal_route["safety_score"]
        dist = optimal_route["distance_km"]
        
        if score > best_score or (score == best_score and dist < shortest_dist):
            best_score = score
            shortest_dist = dist
            best_destination = dest_node.dict()
            best_route = result
            
    if best_route:
        best_route["analysis_timestamp"] = datetime.utcnow().isoformat()
        best_route["selected_destination"] = best_destination
        return best_route
        
    raise HTTPException(status_code=404, detail="No routes could be computed.")
