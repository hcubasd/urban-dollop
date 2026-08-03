from urban_dollop.synth.zones import zones


def test_zero_sigma_is_deterministic_minimal():
    gdf = zones(sigma=0.0)
    assert gdf["zone_id"].tolist() == [1]
    assert gdf.geometry.notna().all()


def test_given_zone_ids_used_as_is():
    gdf = zones(zone_ids=[5, 10, 15])
    assert gdf["zone_id"].tolist() == [5, 10, 15]
    assert len(gdf) == 3
    assert gdf.geometry.notna().all()


def test_given_zone_ids_ignore_sigma_for_count():
    gdf = zones(zone_ids=[1, 2], sigma=5.0)
    assert len(gdf) == 2


def test_pure_synthesis_geometry_always_populated():
    gdf = zones(sigma=1.5)
    assert gdf.geometry.notna().all()
    assert len(gdf) == len(gdf["zone_id"].unique())
