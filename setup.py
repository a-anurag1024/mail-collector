import os

import setuptools.command.build_py
import setuptools.command.develop

from setuptools import find_packages, setup


cwd = os.path.dirname(os.path.abspath(__file__))

# create the basic directory structure
os.makedirs(os.path.join(cwd, "secrets"), exist_ok=True)
os.makedirs(os.path.join(cwd, "mount"), exist_ok=True)

class build_py(setuptools.command.build_py.build_py):  # pylint: disable=too-many-ancestors
    def run(self):
        setuptools.command.build_py.build_py.run(self)


class develop(setuptools.command.develop.develop):
    def run(self):
        setuptools.command.develop.develop.run(self)


requirements = open(os.path.join(cwd, "requirements.txt"), "r").readlines()


with open("README.md", "r", encoding="utf-8") as readme_file:
    README = readme_file.read()


setup(
    name="mail_collector",
    version="1.0.0",
    url="https://github.com/a-anurag1024/mail-collector",
    author="Aditya A Dash",
    author_email="a.anurag1024[at]gmail.com",
    description="wrapper package to interact with gmail API, collect and create mail datasets from personal gmail account",
    long_description=README,
    long_description_content_type="text/markdown",
    license="MIT",
    # package
    packages=find_packages(include=["gmail_collector"]),
    project_urls={
        "Repository": "https://github.com/a-anurag1024/mail-collector"
    },
    cmdclass={
        "build_py": build_py,
        "develop": develop,
        # 'build_ext': build_ext
    },
    install_requires=requirements,
    python_requires=">=3.9.0",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: MIT License",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Dataset Creation",
    ],
    zip_safe=False,
)