# Motor-ODM
[![Build](https://github.com/Codello/Motor-ODM/workflows/Build/badge.svg)](https://github.com/Codello/Motor-ODM/actions?query=workflow%3ABuild)
[![Documentation Status](https://readthedocs.org/projects/motor-odm/badge/?version=latest)](https://motor-odm.readthedocs.io/en/latest/?badge=latest)
[![Codecov](https://img.shields.io/codecov/c/github/Codello/Motor-ODM)](https://codecov.io/gh/Codello/Motor-ODM)
[![Requirements Status](https://requires.io/github/Codello/Motor-ODM/requirements.svg?branch=master)](https://requires.io/github/Codello/Motor-ODM/requirements/?branch=master)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Motor-ODM)](https://pypi.org/project/Motor-ODM/)
[![PyPI](https://img.shields.io/pypi/v/Motor-ODM)](https://pypi.org/project/Motor-ODM/)

![License](https://img.shields.io/github/license/Codello/Motor-ODM)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A MongoDB ODM based on Motor and Pydantic.

The project code is hosted on [GitHub](https://github.com/Codello/Motor-ODM), documentation on [ReadTheDocs](https://motor-odm.readthedocs.io/).


## Installation

```shell script
pip install Motor-ODM
```

## Quick Start
```python
from motor.motor_asyncio import AsyncIOMotorClient
from motor_odm import Document

# Create a custom model by subclassing Document
class User(Document):
    class Mongo:
        # Set the collection name
        collection = "users"
    
    # Add attributes to your model
    username: str
    age: int

# Connect your model to a database
client = AsyncIOMotorClient(...)
Document.use(client.get_default_database())

# Create documents and save them to the database
u = User(username="John", age=20)
await u.insert()

# Query the database
async for user in User.all():
    print(user.username)
```

For a more complete overview have a look at the [docs](https://motor-odm.readthedocs.io/).