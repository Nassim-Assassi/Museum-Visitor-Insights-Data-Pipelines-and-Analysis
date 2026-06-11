def read_input(filename: str) -> list[str]:
    with open(filename, "r") as f:
        return f.readlines()


def remove_new_lines(lines: list[str]) -> list[str]:
    return [line.replace("\n", "") for line in lines]


def convert_lines_to_lists(lines: list[str]) -> list[int]:
    return [int(line) for line in lines]


def get_gamma(lines: list[str]) -> str:
    gamma = ""
    for col in range(len(lines[0])):
        one_count = 0
        for row in lines:
            one_count += int(row[col])
        if one_count > len(lines)/2:
            gamma += "1"
        else:
            gamma += "0"
    return gamma


def get_epsilon(lines: list[str]) -> str:
    epsilon = ""
    gamma = get_gamma(lines)
    for character in gamma:
        if character == "1":
            epsilon += "0"
        else:
            epsilon += "1"
    return epsilon


def binary_to_int(binary: str) -> int:
    total_value = 0
    for index, digit in enumerate(reversed(binary)):
        if digit == "1":
            total_value += (2**index)
    return total_value


def get_submarine_consumption(lines) -> int:
    gamma = get_gamma(lines)
    epsilon = get_epsilon(lines)
    consumption = binary_to_int(gamma) * binary_to_int(epsilon)
    return consumption


if __name__ == "__main__":
    input = read_input("input.txt")
    input = remove_new_lines(input)
    consumption = get_submarine_consumption(input)
    print(consumption)
