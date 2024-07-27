from typing import Iterator


def from_the_middle_out(start:int, end:int) -> Iterator[int]:
    middle_i = (end - start) // 2
    for i in range(end - start):
        yield start + middle_i + ((i + 1) // 2) * (1 if i % 2 == 0 else - 1)