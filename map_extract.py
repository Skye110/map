import geopandas as gpd

PBF_PATH = "mongolia-251026-free/"
OUT_SHP  = "mongolia-251026-free/gis_osm_roads_free_1.shp"


print(" Reading .pbf file...")
gdf = gpd.read_file(PBF_PATH, layer="lines")

print(" File loaded. Filtering highways...")
roads = gdf[gdf["highway"].notna()]
print(f" Total roads: {len(roads)}")
roads.to_file(OUT_SHP)

print("Shapefile written successfully ->", OUT_SHP)
