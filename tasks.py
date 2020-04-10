from invoke import Context, task


@task
def test(c):
    c: Context
    c.run("pytest")


@task
def black(c, check=False):
    c: Context
    if check:
        c.run("black motor_odm --check")
    else:
        c.run("black motor_odm")


@task
def flake8(c):
    c: Context
    c.run("flake8")


@task
def mypy(c):
    c: Context
    c.run("mypy motor_odm")


@task
def isort(c, check=False):
    c: Context
    if check:
        c.run("isort -rc --check-only")
    else:
        c.run("isort -rc")


@task
def format(c):
    c: Context
    print("Formatting with Black...")
    black(c)
    print("Sorting Imports...")
    isort(c)


@task
def lint(c):
    c: Context
    print("Running Black...")
    black(c, check=True)
    print("Running flake8...")
    flake8(c)
    print("Running MyPy...")
    mypy(c)
    print("Running isort...")
    isort(c, check=True)


@task
def make_docs(c):
    c: Context
    c.run("cd docs && make html")
