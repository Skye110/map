from shapely.geometry import LineString
import geopandas as gpd
from collections import defaultdict
from pyproj import Transformer

SNAP_TOLERANCE = 1e-6

def round_coord(coord, tol=SNAP_TOLERANCE):
    return (round(coord[0]/tol)*tol, round(coord[1]/tol)*tol)

class Graph:
    def __init__(self):
        self.adj = defaultdict(list)
        self.coord_to_node = {}
        self.node_coords = {}
        self.node_lonlat = {}
        self.next_node_id = 0

    def get_node(self, coord_graph):
        rc = round_coord(coord_graph)
        if rc in self.coord_to_node:
            return self.coord_to_node[rc]
        nid = self.next_node_id
        self.next_node_id += 1
        self.coord_to_node[rc] = nid
        self.node_coords[nid] = rc
        return nid

    def add_edge(self, a_coord_graph, b_coord_graph, weight=1.0, meta=None, one_way=False):
        a = self.get_node(a_coord_graph)
        b = self.get_node(b_coord_graph)
        self.adj[a].append((b, float(weight), meta))
        if not one_way:
            self.adj[b].append((a, float(weight), meta))

def build_graph_from_shp(shp_path, target_epsg=3857):
    print("Reading...:", shp_path)
    gdf = gpd.read_file(shp_path)
    print("Loaded.:", len(gdf))

    if gdf.crs is None:
        raise ValueError("crs error!.")

    # Reproject if needed
    if target_epsg and getattr(gdf.crs, "to_epsg", lambda: None)() != target_epsg:
        print(f" {gdf.crs}-ees:{target_epsg}")
        gdf = gdf.to_crs(epsg=target_epsg)

    graph_crs = gdf.crs
    to_wgs84 = Transformer.from_crs(graph_crs.to_string(), "EPSG:4326", always_xy=True)

    G = Graph()
    processed_segments = 0
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        
        segments = [geom] if geom.geom_type == "LineString" else list(geom.geoms)
        
        for seg in segments:
            coords = list(seg.coords)
            for i in range(len(coords)-1):
                a = coords[i]
                b = coords[i+1]
                length = LineString([a, b]).length
                G.add_edge(
                    (float(a[0]), float(a[1])), 
                    (float(b[0]), float(b[1])), 
                    weight=float(length)
                )
                processed_segments += 1
        
        if (idx + 1) % 10000 == 0:
            print(f"  Processed {idx + 1}/{len(gdf)} features...")

    print("WGS84...")
    for nid, (x, y) in G.node_coords.items():
        lon, lat = to_wgs84.transform(x, y)
        G.node_lonlat[nid] = (float(lon), float(lat))

    print("✅")
    print(f"   - Nodes: {len(G.node_coords):,}")
    print(f"   - Edges: {sum(len(v) for v in G.adj.values()):,}")
    print(f"   - Segments: {processed_segments:,}")
    
    return G, graph_crs