from day_1 import remove_new_lines, convert_lines_to_int, count_increases, count_increases_sliding


def test_remove_new_lines():
    assert remove_new_lines(["a\n", "a\n", "a\n"]) == ["a", "a", "a"]


def test_convert_lines_to_int():
    assert convert_lines_to_int(["1", "2", "3"]) == [1, 2, 3]


def test_count_increases():
    assert count_increases([199, 200, 208, 210, 200,
                           207, 240, 269, 260, 263]) == 7


def test_count_increases_sliding():
    assert count_increases_sliding([199,
                                    200,
                                    208,
                                    210,
                                    200,
                                    207,
                                    240,
                                    269,
                                    260,
                                    263]) == 5
