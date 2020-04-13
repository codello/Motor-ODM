from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from bson import Code

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny

__all__ = ["Query", "q"]


def q(*args: Any, **kwargs: Any) -> "Query":
    """Creates a MongoDB query from the specified arguments.

    The query can be used to filter documents in Motor-ODM or even directly in Motor or
    PyMongo. This function is the preferred way of constructing queries. You can use
    special keyword arguments to construct more complex queries.

    One of the most common cases is a query by ID. Specify the ID as the only positional
    argument:

    >>> q(123)
    {'_id': 123}

    If you pass ``None`` as the single id value, a query will be constructed that
    matches nothing.
    >>> q(None)
    {'X': {'$in': []}}

    You can also create a query that matches an ID in a list of IDs by specifying
    multiple positional arguments, each of which will be treated as a possible ID. In
    this case ``None`` values will simply be ignored.
    >>> q(123, None, "ABC")
    {'_id': {'$in': [123, 'ABC']}}

    Instead of querying the ID of a document you most likely need to filter documents
    based on their fields. You can do this by providing the respective keyword
    arguments. You can combine positional and keyword arguments if you need to. In the
    simples case we want to create a query that filters on the value of one or more
    fields:

    >>> q(name="John", age=20)
    {'name': 'John', 'age': 20}

    You can also use MongoDB `query operators
    <https://docs.mongodb.com/manual/reference/operator/query/>`_ to create more complex
    queries:

    >>> q(age__gt=20, age__lt=100)
    {'age': {'$gt': 20, '$lt': 100}}

    Lastly you can combine queries with ``&``, ``|`` and ``^``. The ``^`` operator means
    *nor* in this case.

    >>> (q(age=20) & q(name="John")) | q(age=21)
    {'$or': [{'$and': [{'age': 20}, {'name': 'John'}]}, {'age': 21}]}
    """
    return Query(*args, **kwargs)


class QueryExpression(Dict[str, Any]):
    """Helper class for :class:`Query`.

    This helper class is used to identify whether a dictionary is a user-supplied
    document or a combination of query operators used by :class:`Query`.

    :meta private:
    """


class Query(Dict[str, Any]):
    """A MongoDB query.

    Queries behave like ordinary dictionaries (in fact they inherit from :class:`dict`).
    However they offer some additional convenience related to MongoDB queries. Most
    notably they can be constructed conveniently from keyword arguments. See the
    documentation on :func:`q` for details.

    This class also offers some factory methods for special queries such as using a JSON
    Schema.
    """

    @classmethod
    def schema(cls, schema: "DictStrAny") -> "Query":
        """Constructs a ``$jsonSchema`` query."""
        query = Query()
        query.update({"$jsonSchema": schema})
        return query

    @classmethod
    def expr(cls, expression: dict) -> "Query":
        """Constructs an ``$expr`` query."""
        query = Query()
        query.update({"$expr": expression})
        return query

    @classmethod
    def text(
        cls,
        search: str,
        language: str = None,
        case_sensitive: bool = None,
        diacritic_sensitive: bool = None,
    ) -> "Query":
        """Constructs a ``$text`` query using the specified arguments."""
        text: Dict[str, Union[str, bool]] = {"$search": search}
        if language is not None:
            text["$language"] = language
        if case_sensitive is not None:
            text["$caseSensitive"] = case_sensitive
        if diacritic_sensitive is not None:
            text["$diacriticSensitive"] = diacritic_sensitive
        query = Query()
        query.update({"$text": text})
        return query

    @classmethod
    def where(cls, where: Union[str, Code]) -> "Query":
        """Constructs a ``$where`` query."""
        query = Query()
        query.update({"$where": where})
        return query

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """ Creates a new query.

        This constructor accepts the same arguments as the :func:`q` function. See the
        documentation on the :func:`q` function for details.
        """
        super().__init__()
        if len(args) == 1:
            id_value = args[0]
            if id_value is None:
                # Return a query that matches nothing if id_value is None
                self["X"] = {"$in": []}
            else:
                self["_id"] = id_value
        elif len(args) > 1:
            ids = [arg for arg in args if arg is not None]
            self["_id"] = {"$in": ids}
        self.extend(**kwargs)

    def extend(self, **kwargs: "DictStrAny") -> None:
        """Adds fields to this query.

        This method adds the same keys and values that you would get using the :func:`q`
        function with only keyword arguments. See the documentation on that method for
        details.
        """
        for key, value in kwargs.items():
            if "__" not in key:
                self.add_expression(key, value)
            else:
                [key, op] = key.rsplit("__", 1)
                self.add_expression(key, value, op=op)

    def add_expression(self, field: str, value: Any, op: str = None) -> None:
        """Adds a single expression to this query.

        An expression is a constraint for a single field. This method modifies the query
        to add a constraint for the specified ``field`` to be equal to ``value``. If
        ``op`` is specified it is used instead of the default ``$eq`` operator.

        :raises KeyError: If ``field`` has already a value for ``op`` that is not equal
                          to ``value``.
        """
        if field not in self and op is None:
            self[field] = value
            return
        existing = self.setdefault(field, QueryExpression())
        if isinstance(existing, QueryExpression):
            expression = existing
        else:
            expression = QueryExpression({"$eq": existing})
        if op is None and "$eq" in expression:
            if expression["$eq"] == value:
                return
            value1 = str(value)
            value2 = str(expression["$eq"])
            raise ValueError(
                f"Conflicting equality constraints: "
                f"{', '.join([f'{field}={value1}', f'{field}={value2}'])}"
            )
        op = _transform_op(op)
        if op in expression and expression[op] != value:
            value1 = str(value)
            value2 = str(expression[op])
            raise ValueError(
                f"Conflicting constraints for field {field}: "
                f"{', '.join([f'{op}={value1}', f'{op}={value2}'])}"
            )
        expression[op] = value
        self[field] = expression

    def comment(self, comment: str) -> "Query":
        """Adds a comment to this query."""
        self["$comment"] = comment
        return self

    def __and__(self, other: dict) -> "Query":
        assert isinstance(other, dict)
        query = Query()
        query.update({"$and": [self, other]})
        return query

    def __or__(self, other: dict) -> "Query":
        assert isinstance(other, dict)
        query = Query()
        query.update({"$or": [self, other]})
        return query

    def __xor__(self, other: dict) -> "Query":
        assert isinstance(other, dict)
        query = Query()
        query.update({"$nor": [self, other]})
        return query


def _transform_op(op: Optional[str]) -> str:
    """Transforms an operator for MongoDB compatibility.

    This method takes an operator (as specified in a keyword argument) and transforms it
    to a ``$`` prefixed camel case operator for MongoDB.
    """
    if op is None:
        return "$eq"

    camel = op[0].lower() + op.title()[1:].replace("_", "")
    return f"${camel}"
