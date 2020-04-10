from invoke import Context, task


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
def lint(c):
    c: Context
    print("Running flake8")
    flake8(c)
    print("Running MyPy")
    mypy(c)
    print("Running isort")
    isort(c, check=True)
