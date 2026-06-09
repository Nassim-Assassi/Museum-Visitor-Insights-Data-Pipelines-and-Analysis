def read_input(filename: str) -> list[str]:
    with open(filename, "r") as f:
        return f.readlines()


def remove_new_lines(lines: list) -> list:
    return [line.replace("\n", "") for line in lines]


def convert_movement_strings_to_tuples(lines: list) -> list:
    return [tuple(line.split(" ")) for line in lines]


def convert_distance_to_int(lines: list[tuple]) -> list[tuple]:
    return [(line[0], int(line[1])) for line in lines]


def get_hor_and_dep(movements: list[tuple]):
    horizontal = 0
    depth = 0
    for movement in movements:
        if movement[0] == "forward":
            horizontal += movement[1]
        if movement[0] == "up":
            depth -= movement[1]
        if movement[0] == "down":
            depth += movement[1]
    return (horizontal, depth)


def multiply_tuple(values: tuple) -> int:
    return values[0]*values[1]


def part_2_get_hor_and_dep(movements):
    aim = 0
    horizontal = 0
    depth = 0

    for movement in movements:
        if movement[0] == "forward":
            horizontal += movement[1]
            depth += movement[1]*aim
        if movement[0] == "up":
            aim -= movement[1]
        if movement[0] == "down":
            aim += movement[1]

    return (horizontal, depth)


if __name__ == "__main__":
    input = read_input("input.txt")
    input = remove_new_lines(input)
    input = convert_movement_strings_to_tuples(input)
    input = convert_distance_to_int(input)
    position = part_2_get_hor_and_dep(input)
    multiplied = multiply_tuple(position)
    print(multiplied)
