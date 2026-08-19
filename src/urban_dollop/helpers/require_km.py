import pyproj

# A local, unanchored Cartesian plane whose unit is the kilometre --
# +units=km is a real, PROJ-recognized linear unit (unit_conversion_factor
# 1000.0 to metres, confirmed against pyproj directly), not a custom hack.
# Nothing downstream of require_km needs to know *where on Earth* the data
# is -- COPERT, BPR, and every distance comparison in this pipeline only
# ever care about relative distances -- so dropping the real-world anchor
# costs nothing. This exists purely so a rescaled GeoDataFrame still carries
# a real, valid CRS rather than a stale or absent one; require_km's result
# is always a transient in-memory copy, never written back to a file, so no
# other code ever needs to resolve this CRS against a real place.
_KM_CRS = pyproj.CRS.from_user_input(
    "+proj=etmerc +lat_0=0 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=km +no_defs"
)


def require_km(gdf, path):
    """`gdf` with its geometry column rescaled so its raw coordinate values
    are directly kilometres, and every downstream consumer -- a link's own
    `.length`, a `consolidation_radii` comparison between two points, the
    network's own KD-tree match against a desire line's origin -- can
    trust that number with no unit bookkeeping of its own. Always a
    transient, in-memory result: never written back to a file, so its own
    CRS never has to be resolved against anything real again.

    Requires a real CRS and raises otherwise. There is no fallback that
    guesses from the coordinates' own magnitude: a file with no CRS is
    exactly indistinguishable from one that's honestly already in km, and
    a wrong guess there is silently wrong distance and emissions data --
    worse than the loud failure this raises instead. This is not
    optional strictness for its own sake: network_emissions.py's COPERT
    formula is calibrated against real km/h and grams/km, so every
    geometry-bearing file in the pipeline -- zones, network, agents,
    desire lines, synthesized or real -- has to agree on the same real
    unit for any of them to be correct once they're used together, not
    just internally consistent with themselves.

    Two cases, both fully deterministic, neither a heuristic:
      - A projected CRS carries a real linear unit (metre, US survey
        foot, ...). Its exact conversion factor to metres is read
        straight off the CRS -- no reprojection needed, just a scale.
      - A geographic CRS (lat/lon) has no fixed conversion at all -- a
        degree of longitude is a different real distance depending on
        latitude -- so it's reprojected first, into the UTM zone
        geopandas picks from the data's own centroid, which *does* carry
        a real linear unit, and then scaled the same way.
    """
    if gdf.crs is None:
        raise ValueError(
            f"{path}: no CRS set. Every geometry file has to carry a real CRS -- "
            "there's no way to tell a file that's honestly already in km apart from "
            "one that silently isn't, so this is rejected outright rather than guessed at."
        )

    metric = gdf if not gdf.crs.is_geographic else gdf.to_crs(gdf.estimate_utm_crs())
    factor = metric.crs.axis_info[0].unit_conversion_factor  # metric's own unit -> metres
    km = metric.copy()
    km["geometry"] = metric.geometry.affine_transform([factor / 1000, 0, 0, factor / 1000, 0, 0])
    km = km.set_crs(_KM_CRS, allow_override=True)
    return km
