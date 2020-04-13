import math

import pytest

from motor_odm import Query, q

TEST_OPERATORS = ["lt", "gt", "eq", "neq", "abc"]


@pytest.fixture(scope="function")
def query():
    return q(name="Name", age__lt=100, age__gt=20)


def test_instance():
    assert isinstance(q(), Query)


@pytest.mark.parametrize("id", [123, "An ID", 5.4])
def test_single_id(id):
    assert q(id) == {"_id": id}


def test_none_id():
    assert q(None) == {"_id": math.nan}


def test_multi_id():
    assert q(123, None, "Some ID") == {"_id": {"$in": [123, "Some ID"]}}


def test_kwargs():
    assert q(name="Name", password="Value") == {"name": "Name", "password": "Value"}


@pytest.mark.parametrize("op", TEST_OPERATORS)
def test_operator(op):
    assert q(**{f"age__{op}": 20}) == {"age": {f"${op}": 20}}


def test_multiple_operators():
    assert q(age__gt=20, age__lt=100) == {"age": {"$gt": 20, "$lt": 100}}


def test_independent_fields():
    assert q(name="Name", age__lt=100) == {"name": "Name", "age": {"$lt": 100}}


def test_camel_operators():
    assert q(mask__bits_all_set=15) == {"mask": {"$bitsAllSet": 15}}


def test_auto_eq_operator():
    assert q(age=20, age__lt=50) == {"age": {"$eq": 20, "$lt": 50}}


def test_double_eq_same():
    # We want an equality query but the spec does not force a specific query shape
    assert q(age=20, age__eq=20) in [{"age": 20}, {"age": {"$eq": 20}}]


def test_double_eq_different():
    with pytest.raises(ValueError):
        q(age=20, age__eq=21)


def test_extend_eq(query):
    query.extend(surname="Surname")
    assert query == {
        "surname": "Surname",
        "name": "Name",
        "age": {"$gt": 20, "$lt": 100},
    }


def test_extend_eq_same(query):
    query.extend(name="Name")
    assert query == {
        "name": "Name",
        "age": {"$gt": 20, "$lt": 100},
    }


def test_extend_eq_conflict(query):
    with pytest.raises(ValueError):
        query.extend(name="Name 2")


def test_extend_op(query):
    query.extend(name__lt="ZZZZ")
    assert query == {
        "name": {"$eq": "Name", "$lt": "ZZZZ"},
        "age": {"$gt": 20, "$lt": 100},
    }


def test_extend_op_same(query):
    query.extend(age__lt=100)
    assert query == {
        "name": "Name",
        "age": {"$gt": 20, "$lt": 100},
    }


def test_extend_op_conflict(query):
    with pytest.raises(ValueError):
        query.extend(age__lt=25)


def test_json_schema():
    query = Query.schema({"ABC": "DEF"})
    assert query == {"$jsonSchema": {"ABC": "DEF"}}


def test_text_query():
    query = Query.text("abc")
    assert query == {"$text": {"$search": "abc"}}
    query = Query.text("abc", case_sensitive=True)
    assert query == {"$text": {"$search": "abc", "$caseSensitive": True}}
    query = Query.text("abc", diacritic_sensitive=False)
    assert query == {"$text": {"$search": "abc", "$diacriticSensitive": False}}
    query = Query.text("abc", language="none")
    assert query == {"$text": {"$search": "abc", "$language": "none"}}


def test_comment(query):
    assert query.comment("A Comment") == {
        "name": "Name",
        "age": {"$gt": 20, "$lt": 100},
        "$comment": "A Comment",
    }
