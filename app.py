from flask import Flask, request, jsonify, render_template
from build_graph import build_graph_from_shp
from algorithms import bfs_shortest, dfs_path_safe, dijkstra, enumerate_paths_dfs
from pyproj import Transformer
import os, logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("routefinder")

app = Flask(__name__, template_folder="templates", static_folder="static")
SHP_PATH = os.environ.get("OSM_SHP", "mongolia-251026-free/gis_osm_roads_free_1.shp")
log.info("Main: loading graph from %s", SHP_PATH)
G, graph_crs = build_graph_from_shp(SHP_PATH)
log.info("Main: graph loaded: nodes=%d adj_entries=%d", len(G.node_coords), sum(len(v) for v in G.adj.values()))

transformer_to_graph = Transformer.from_crs("EPSG:4326", graph_crs.to_string(), always_xy=True)

def nearest_node(graph, x, y):
    best, best_d = None, float("inf")
    for nid, (nx, ny) in graph.node_coords.items():
        d = (nx - x)**2 + (ny - y)**2
        if d < best_d:
            best, best_d = nid, d
    return best

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/route")
def route():
    src = request.args.get("src")
    dst = request.args.get("dst")
    mode = request.args.get("mode", "shortest")
    alg = (request.args.get("alg") or "").lower()
    
    try:
        max_paths = int(request.args.get("max_paths", 50))
    except:
        max_paths = 50
    try:
        max_depth = int(request.args.get("max_depth", 500))
    except:
        max_depth = 500
    max_weight_param = request.args.get("max_weight", None)
    try:
        max_weight = float(max_weight_param) if max_weight_param is not None else None
    except:
        max_weight = None

    if not src or not dst:
        return jsonify(error="src and dst required (lon,lat)"), 400
    
    try:
        lon1, lat1 = map(float, src.split(","))
        lon2, lat2 = map(float, dst.split(","))
    except Exception as e:
        return jsonify(error=f"bad src/dst format: {e}"), 400

    try:
        gx1, gy1 = transformer_to_graph.transform(lon1, lat1)
        gx2, gy2 = transformer_to_graph.transform(lon2, lat2)
    except Exception:
        gx1, gy1, gx2, gy2 = lon1, lat1, lon2, lat2

    s = nearest_node(G, gx1, gy1)
    t = nearest_node(G, gx2, gy2)
    
    if s is None or t is None:
        return jsonify(error="nearest node not found"), 400

    note = None
    
    try:
        if mode == "all":
            if alg and alg != "dfs":
                note = f"'{alg}' requested, using DFS enumeration for finding multiple paths."
            if max_weight is None:
                try:
                    _, dist = dijkstra(G, s, t)
                    if dist and dist != float("inf"):
                        max_weight = dist * 1.5
                except:
                    pass
            
            paths = enumerate_paths_dfs(G, s, t,
                                      max_paths=max_paths, 
                                      max_depth=max_depth, 
                                      max_total_weight=max_weight)
            
            out = []
            for p_nodes, weight in paths:
                out.append({"path": [G.node_lonlat[n] for n in p_nodes], "weight": weight})
            
            return jsonify({
                "mode": "all", 
                "algorithm": "DFS_enumerate", 
                "paths": out, 
                "count": len(out),
                "note": note
            })

        if mode == "minsteps":
            if alg in ("", "bfs"):
                path_nodes = bfs_shortest(G, s, t)
                used_alg = "BFS"
            elif alg == "dijkstra":
                path_nodes, _ = dijkstra(G, s, t)
                used_alg = "Dijkstra"
                note = "Using Dijkstra for weighted shortest path; BFS typically finds fewest edges."
            elif alg == "dfs":
                path_nodes = dfs_path_safe(G, s, t, max_nodes=1000000, max_depth=5000)
                used_alg = "DFS"
                note = "Using DFS; does not guarantee fewest edges."
            else:
                path_nodes = bfs_shortest(G, s, t)
                used_alg = "BFS"
                note = f"Unknown algorithm '{alg}' — defaulted to BFS."
            
            if not path_nodes:
                return jsonify({"mode": "minsteps", "algorithm": used_alg, "error": "no path found", "note": note})
            
            coords = [G.node_lonlat[n] for n in path_nodes]
            return jsonify({"mode": "minsteps", "algorithm": used_alg, "path": coords, "note": note})

        if mode == "shortest":
            if alg in ("", "dijkstra"):
                path_nodes, dist = dijkstra(G, s, t)
                used_alg = "Dijkstra"
            elif alg == "bfs":
                path_nodes = bfs_shortest(G, s, t)
                dist = None
                used_alg = "BFS"
                note = "BFS minimizes edges, not necessarily distance."
            elif alg == "dfs":
                path_nodes = dfs_path_safe(G, s, t, max_nodes=1000000, max_depth=5000)
                dist = None
                used_alg = "DFS"
                note = "DFS does not guarantee shortest distance."
            else:
                path_nodes, dist = dijkstra(G, s, t)
                used_alg = "Dijkstra"
                note = f"Unknown algorithm '{alg}' — defaulted to Dijkstra."
            
            if not path_nodes:
                return jsonify({"mode": "shortest", "algorithm": used_alg, "error": "no path found", "note": note})
            
            coords = [G.node_lonlat[n] for n in path_nodes]
            out = {"mode": "shortest", "algorithm": used_alg, "path": coords}
            if dist is not None:
                out["distance"] = round(dist, 3)
            if note:
                out["note"] = note
            return jsonify(out)

        return jsonify({"error": "unknown mode"})

    except Exception as ex:
        log.exception("Error processing route")
        return jsonify(error=f"processing error: {str(ex)}"), 500

@app.route("/compare")
def compare():
    src = request.args.get("src")
    dst = request.args.get("dst")
    alg = (request.args.get("alg") or "").lower()
    
    if not src or not dst:
        return jsonify(error="src and dst required (lon,lat)"), 400
    
    try:
        lon1, lat1 = map(float, src.split(","))
        lon2, lat2 = map(float, dst.split(","))
    except Exception as e:
        return jsonify(error=f"bad src/dst format: {e}"), 400

    gx1, gy1 = transformer_to_graph.transform(lon1, lat1)
    gx2, gy2 = transformer_to_graph.transform(lon2, lat2)
    s = nearest_node(G, gx1, gy1)
    t = nearest_node(G, gx2, gy2)
    
    if s is None or t is None:
        return jsonify(error="nearest node not found"), 400

    results = []
    
    try:
        path_nodes, dist = dijkstra(G, s, t)
        if path_nodes:
            coords = [G.node_lonlat[n] for n in path_nodes]
            results.append({
                "mode": "shortest",
                "algorithm": "Dijkstra",
                "path": coords,
                "distance": round(dist, 3) if dist else None
            })
        else:
            results.append({"mode": "shortest", "error": "no path found"})
    except Exception as ex:
        results.append({"mode": "shortest", "error": str(ex)})
    
    try:
        path_nodes = bfs_shortest(G, s, t)
        if path_nodes:
            coords = [G.node_lonlat[n] for n in path_nodes]
            results.append({
                "mode": "minsteps",
                "algorithm": "BFS",
                "path": coords
            })
        else:
            results.append({"mode": "minsteps", "error": "no path found"})
    except Exception as ex:
        results.append({"mode": "minsteps", "error": str(ex)})
    
    try:
        _, dist = dijkstra(G, s, t)
        max_weight = dist * 1.5 if dist and dist != float("inf") else None
        paths = enumerate_paths_dfs(G, s, t, max_paths=20, max_depth=300, max_total_weight=max_weight)
        out = []
        for p_nodes, weight in paths:
            out.append({"path": [G.node_lonlat[n] for n in p_nodes], "weight": weight})
        results.append({
            "mode": "all",
            "algorithm": "DFS_enumerate",
            "paths": out,
            "count": len(out)
        })
    except Exception as ex:
        results.append({"mode": "all", "error": str(ex)})
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)