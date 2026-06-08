def read_input(filename: str) -> list[str]:
    with open(filename, "r") as f:
        return f.readlines()


def remove_new_lines(lines: list) -> list:
    return [line.replace("\n", "") for line in lines]


def convert_lines_to_int(lines: list) -> list:
    return [int(line) for line in lines]


def count_increases(values) -> int:
    count = 0
    previous_value = "n/a"
    for value in values:
        if previous_value != "n/a":
            if value > previous_value:
                count += 1
        previous_value = value
    return count


def count_increases_sliding(values):
    count = 0
    previous_sum = "n/a"
    previous_value_2 = "n/a"
    previous_value_1 = "n/a"
    for current_value in values:
        if previous_value_1 != "n/a" and previous_value_2 != "n/a":
            current_sum = current_value + previous_value_1 + previous_value_2
            if previous_sum != "n/a":
                if current_sum > previous_sum:
                    count += 1
            previous_sum = current_sum
        previous_value_2 = previous_value_1
        previous_value_1 = current_value

    return count


def depth_increase_counter(depths: list[int]) -> int:
    count = 0
    cur_depth = depths[0]
    for d in range(len(depths)):
        if depths[d] > cur_depth:
            count += 1
        cur_depth = depths[d]
    if depths[len(depths)-1] > cur_depth:
        count += 1
    return count, cur_depth


if __name__ == "__main__":
    input = read_input("input.txt")
    input = remove_new_lines(input)
    input = convert_lines_to_int(input)
    count = count_increases(input)
    print(count)
