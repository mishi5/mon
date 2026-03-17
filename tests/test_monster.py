from models.monster import calc_hp, calc_stat, exp_to_next


def test_calc_hp_level_1():
    # HP = floor(base * 1 / 50) + 1 + 10
    assert calc_hp(base=45, level=1) == 11  # floor(45/50) + 1 + 10 = 0 + 11


def test_calc_hp_level_10():
    # HP = floor(45 * 10 / 50) + 10 + 10 = 9 + 20 = 29
    assert calc_hp(base=45, level=10) == 29


def test_calc_stat_level_1():
    # stat = floor(50 * 1 / 50) + 5 = 1 + 5 = 6
    assert calc_stat(base=50, level=1) == 6


def test_calc_stat_level_10():
    # stat = floor(50 * 10 / 50) + 5 = 10 + 5 = 15
    assert calc_stat(base=50, level=10) == 15


def test_exp_to_next_level_1():
    # level^3 - (level-1)^3 = 1 - 0 = 1
    assert exp_to_next(1) == 1


def test_exp_to_next_level_5():
    # 5^3 - 4^3 = 125 - 64 = 61
    assert exp_to_next(5) == 61


def test_exp_to_next_level_10():
    # 10^3 - 9^3 = 1000 - 729 = 271
    assert exp_to_next(10) == 271
