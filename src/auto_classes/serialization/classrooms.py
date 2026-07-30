from auto_classes.core import Classroom


def dump_classrooms(classrooms: list[Classroom]) -> list[dict[str, object]]:
    return [{"name": classroom.name, "tags": sorted(classroom.tags)} for classroom in classrooms]


def load_classrooms(data: list[dict[str, object]]) -> list[Classroom]:
    classrooms = [Classroom(name=item["name"], tags=set(item["tags"])) for item in data]
    names = [classroom.name for classroom in classrooms]
    if len(names) != len(set(names)):
        raise ValueError("Les noms de classe doivent être uniques")
    return classrooms
