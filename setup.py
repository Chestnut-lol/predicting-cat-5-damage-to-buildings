from setuptools import find_packages, setup

setup(
    name="src",
    version="0.0.1",
    author="Alice",
    author_email="author@example.com",
    description="This is to set up the groundwork and provide framework code",
    url="url-to-github-page",
    packages=find_packages(),
    test_suite="src.tests.test_all.suite",
)
