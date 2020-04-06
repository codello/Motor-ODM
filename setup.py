import os

from setuptools import setup, find_packages


def long_description():
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        return f.read()


setup(
    name='Motor-ODM',
    url='https://github.com/Codello/Motor-ODM/',
    license='MIT',
    author='Kim Wittenburg',
    author_email='codello@wittenburg.kim',
    description='A MongoDB ODM based on Motor and Pydantic.',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    keywords="MongoDB AsyncIO ODM Pydantic",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'PyMongo',
        'Motor',
        'Pydantic',
        'Funcy'
    ],
    extras_require={
        'dev': [
            'pytest'
        ]
    },
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
