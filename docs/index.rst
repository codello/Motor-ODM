Motor-ODM |version| Documentation
=================================

Overview
--------
Motor-ODM is a modern async Object-Document-Mapper for MongoDB. It is based on
`Pydantic <https://pydantic-docs.helpmanual.io>`_ and `Motor <https://motor.readthedocs.io/en/stable/>`_. It exclusively
works with :mod:`asyncio`.

Using :class:`ObjectId <bson.objectid.ObjectId>`
------------------------------------------------

If you are using Pydantic for more than your ODM (e.g. when using `FastAPI <https://fastapi.tiangolo.com>`_ and want to
use the :class:`bson.ObjectId <bson.objectid.ObjectId>` class you need to tell Pydantic how to handle this class. You
can either do this manually or use the handlers from Motor-ODM. To do so all you need to do is make sure that
:mod:`motor_odm.document` is imported before you define your Pydantic models that use
:class:`ObjectId <bson.objectid.ObjectId>`.

API-Documentation
-----------------
Motor-ODM consists of several modules and classes all of which are documented in the full
:doc:`API reference <reference/motor_odm>`. This section highlights some classes in order to give you an overview where
to start.

.. autosummary::
   :nosignatures:

   motor_odm.document.Document


.. toctree::
   :caption: Table of Contents
   :name: Contents

   Motor-ODM Documentation <self>
   API Reference <reference/motor_odm>
   genindex
