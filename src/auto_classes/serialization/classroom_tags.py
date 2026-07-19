def dump_classroom_tags(classroom_tags: list[set[str]]) -> list[list[str]]:
    return [sorted(tags) for tags in classroom_tags]


def load_classroom_tags(data: list[list[str]]) -> list[set[str]]:
    return [set(tags) for tags in data]
