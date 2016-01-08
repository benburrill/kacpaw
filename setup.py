from distutils.core import setup

setup(
    name="KACPAW",
    version="0.0.2",
    author="Ben Burrill",
    packages=["kacpaw"],
    license="LICENSE",
    description="API Wrapper for the Khan Academy Computer Programming section",
    install_requires=[
        "requests >= 2.7.0"
    ]
)