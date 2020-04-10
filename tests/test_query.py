import pytest

from motor_odm.query import create_query


def test_single_kwargs_query():
    query = create_query(username="test")
    assert query == {"username": "test"}


def test_multi_kwargs_query():
    query = create_query(username="test", password="abc")
    assert query == {"username": "test", "password": "abc"}


def test_filter():
    filter = {"something": "value", "more": {"subkey": "subvalue"}}
    query = create_query(filter)
    assert query == filter


@pytest.mark.parametrize("id", [123, "some id", 5.4])
def test_id(id):
    query = create_query(id)
    assert query == {"_id": id}


def test_id_and_kwargs():
    query = create_query(123, username="test", password="abc")
    assert query == {"_id": 123, "username": "test", "password": "abc"}


def test_filter_and_kwargs():
    query = create_query({"some": "field"}, username="test")
    assert query == {"some": "field", "username": "test"}
