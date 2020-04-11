from invoke import Context, task


@task
def test(c, coverage=False):
    c: Context
    args = ["pytest"]
    if coverage:
        args.extend(["--cov", "--cov-report=xml", "--cov-report=html"])
    c.run(" ".join(args), pty=True)


@task
def doctest(c):
    c: Context
    c.run("pytest --doctest-modules --doctest-continue-on-failure motor_odm", pty=True)


@task
def black(c, check=False):
    c: Context
    if check:
        c.run("black motor_odm --check", pty=True)
    else:
        c.run("black motor_odm", pty=True)


@task
def flake8(c):
    c: Context
    c.run("flake8", pty=True)


@task
def mypy(c):
    c: Context
    c.run("mypy motor_odm", pty=True)


@task
def isort(c, check=False):
    c: Context
    if check:
        c.run("isort -rc --check-only", pty=True)
    else:
        c.run("isort -rc", pty=True)


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
def build_docs(c):
    c: Context
    c.run("cd docs && make html", pty=True)


@task
def clean(c):
    c: Context
    files = [
        "build",
        "dist",
        "Motor_ODM.egg-info",
        "pip-wheel-metadata",
        "docs/build",
        "docs/reference",
        ".mypy_cache",
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "coverage.xml",
    ]
    args = ["rm", "-rf", *files]
    c.run(" ".join(args))
