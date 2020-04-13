from invoke import Context, task


@task
def lint(c):
    c: Context
    print("Running flake8...")
    c.run("flake8")
    print("Running MyPy...")
    c.run("mypy motor_odm", pty=True)


@task
def format(c):
    c: Context
    print("Formatting with Black...")
    c.run("black motor_odm", pty=True)
    print("Sorting Imports...")
    c.run("isort -rc", pty=True)


@task
def test(c, coverage=False):
    c: Context
    args = ["pytest"]
    if coverage:
        args.extend(["--cov", "--cov-report=xml", "--cov-report=html"])
    c.run(" ".join(args), pty=True)


@task
def build_docs(c):
    c: Context
    c.run("cd docs && make html", pty=True)


@task
def doctest(c):
    c: Context
    c.run("pytest --doctest-modules --doctest-continue-on-failure motor_odm", pty=True)


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
