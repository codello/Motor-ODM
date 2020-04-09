:orphan:

API Documentation for :mod:`motor_odm`
======================================

.. automodule:: motor_odm

.. data:: ObjectId

   Alias for :class:`bson.ObjectId <bson.objectid.ObjectId>`. It is recommended to use this instead of
   :class:`bson.ObjectId <bson.objectid.ObjectId>` in order to enable support for validation in Pydantic models. This is
   only relevant if you intend to use an :class:`ObjectID` with Pydantic models that are not part of your ODM.

.. toctree::
   :maxdepth: 2
   :glob:

   *
