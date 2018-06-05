from setuptools import setup, find_packages

setup(
    name="Products.ZMySQLDA",
    version="4.0.dev0",
    license="Zope Public License (ZPL) Version 1.0",
    author="HOFFMANN+LIEBENBERG in association with "
            "SNTL Publishing, Andy Dustman, John Eikenberry",
    author_email="zms@sntl-publishing.com",
    url="https://github.com/zms-publishing/Products.ZMySQLDA",
    description="MySQL Zope adapter.",
    long_description=(
        "MySQL Database Adapter for Zope."
    ),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Zope :: 4",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=["Products"],
    zip_safe=False,
    install_requires=[
        "mysqlclient",
        "Zope",
        "Products.ZSQLMethods",
    ]
)
