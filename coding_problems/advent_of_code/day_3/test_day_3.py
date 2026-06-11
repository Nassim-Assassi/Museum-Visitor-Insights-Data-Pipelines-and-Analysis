from day_3 import get_gamma, get_epsilon, binary_to_int, get_submarine_consumption


def test_get_gamma():
    assert get_gamma(["00100",
                     "11110",
                      "10110",
                      "10111",
                      "10101",
                      "01111",
                      "00111",
                      "11100",
                      "10000",
                      "11001",
                      "00010",
                      "01010"]) == "10110"


def test_get_epsilon():
    assert get_epsilon(["00100",
                        "11110",
                        "10110",
                        "10111",
                        "10101",
                        "01111",
                        "00111",
                        "11100",
                        "10000",
                        "11001",
                        "00010",
                        "01010"]) == "01001"


def test_binary_to_int():
    assert binary_to_int("10110") == 22
    assert binary_to_int("01001") == 9


def test_get_submarine_consumption():
    assert get_submarine_consumption(["00100",
                                     "11110",
                                      "10110",
                                      "10111",
                                      "10101",
                                      "01111",
                                      "00111",
                                      "11100",
                                      "10000",
                                      "11001",
                                      "00010",
                                      "01010"]) == 198
