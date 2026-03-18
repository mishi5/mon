from data.type_chart import get_effectiveness


def test_fire_vs_grass_is_super_effective():
    assert get_effectiveness("fire", "grass") == 2.0


def test_fire_vs_water_is_not_very_effective():
    assert get_effectiveness("fire", "water") == 0.5


def test_fire_vs_fire_is_not_very_effective():
    assert get_effectiveness("fire", "fire") == 0.5


def test_normal_vs_ghost_is_immune():
    assert get_effectiveness("normal", "ghost") == 0.0


def test_water_vs_ground_is_super_effective():
    assert get_effectiveness("water", "ground") == 2.0


def test_dual_type_multiplier():
    # Fire vs Grass/Bug: 2.0 * 2.0 = 4.0
    assert get_effectiveness("fire", "grass", "bug") == 4.0


def test_dual_type_cancel():
    # Ground vs Fire/Flying: 2.0 * 0.0 (immune) = 0.0
    assert get_effectiveness("ground", "fire", "flying") == 0.0
