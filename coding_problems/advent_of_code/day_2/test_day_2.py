from day_2 import convert_movement_strings_to_tuples, convert_distance_to_int, get_hor_and_dep, multiply_tuple, part_2_get_hor_and_dep


def test_convert_movement_strings_to_tuples():
    assert convert_movement_strings_to_tuples(
        ["forward 2", "forward 5"]) == [("forward", "2"),  ("forward", "5")]


def test_convert_distance_to_int():
    assert convert_distance_to_int(
        [("forward", "2"),  ("forward", "5")]) == [("forward", 2),  ("forward", 5)]


def test_get_hor_and_dep():
    assert get_hor_and_dep(
        [("forward", 2),  ("forward", 5), ("down", 5), ("up", 1)]) == (7, 4)


def test_multiply_tuple():
    assert multiply_tuple((3, 5)) == 15


def test_part_2_get_hor_and_dep():
    assert part_2_get_hor_and_dep(
        [("forward", 5),  ("down", 5), ("forward", 8), ("up", 3), ("down", 8), ("forward", 2)]) == (15, 60)
