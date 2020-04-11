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
