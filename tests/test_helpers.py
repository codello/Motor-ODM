from motor_odm.helpers import inherit_class


def test_mongo_inherit():
    class Base:
        parent_field = "Parent"
        field = "Test"

    class Child:
        child_field = "Child"
        field = "Test 2"

    New = inherit_class("Meta", Child, Base)

    assert New.__name__ == "Meta"
    assert New.child_field == "Child"
    assert New.parent_field == "Parent"
    assert New.field == "Test 2"


def test_merge_fields_lists():
    class Base:
        __merge__ = {"field"}
        field = ["A", "B"]

    class Child:
        field = ["B", "C"]

    New = inherit_class("Meta", Child, Base)
    assert New.field == ["A", "B", "B", "C"]


def test_merge_fields_sets():
    class Base:
        __merge__ = {"field"}
        field = {"A", "B"}

    class Child:
        field = {"B", "C"}

    New = inherit_class("Meta", Child, Base)
    assert New.field == {"A", "B", "C"}


def test_merge_fields_dicts():
    class Base:
        __merge__ = {"field"}
        field = {"A": "B"}

    class Child:
        field = {"C": "D"}

    New = inherit_class("Meta", Child, Base)
    assert New.field == {"A": "B", "C": "D"}


def test_merge_transitive():
    class Base:
        __merge__ = {"field"}
        field = {"A", "B"}

    class Child:
        __merge__ = {"value"}
        field = {"B", "C"}
        value = [1, 2]

    class ChildChild:
        field = {"D"}
        value = [3]

    New = inherit_class("Meta", Child, Base)
    NewNew = inherit_class("Meta", ChildChild, New)
    assert NewNew.__merge__ == {"field", "value"}
    assert NewNew.field == {"A", "B", "C", "D"}
    assert NewNew.value == [1, 2, 3]
