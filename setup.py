"""
Motor ODM
---------

A MongoDB ODM based on Motor and Pydantic.
"""

from setuptools import setup
from setuptools_scm.version import ScmVersion, guess_next_dev_version


def format_version(version: ScmVersion):
    version.node = None
    return guess_next_dev_version(version)


setup(
    name='Motor-ODM',
    url='https://github.com/Codello/Motor-ODM/',
    license='MIT',
    author='Kim Wittenburg',
    author_email='codello@wittenburg.kim',
    description='A MongoDB ODM based on Motor and Pydantic.',
    long_description=__doc__,
    keywords="MongoDB AsyncIO ODM Pydantic",
    packages=["motor_odm"],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'PyMongo',
        'Motor',
        'Pydantic',
        'Funcy'
    ],
    use_scm_version={
        "version_scheme": format_version
    },
    setup_requires=['wheel', 'setuptools_scm'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
