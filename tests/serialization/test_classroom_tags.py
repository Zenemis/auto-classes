from auto_classes.serialization.classroom_tags import dump_classroom_tags, load_classroom_tags


def test_dump_classroom_tags_sorts_tags_and_keeps_classroom_order() -> None:
    assert dump_classroom_tags([{"latin", "avancé"}, set()]) == [["avancé", "latin"], []]


def test_load_classroom_tags_returns_sets_in_order() -> None:
    assert load_classroom_tags([["latin"], []]) == [{"latin"}, set()]


def test_dump_then_load_round_trips() -> None:
    classroom_tags = [{"latin", "avancé"}, set(), {"espagnol"}]
    assert load_classroom_tags(dump_classroom_tags(classroom_tags)) == classroom_tags
