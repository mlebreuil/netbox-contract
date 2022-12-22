from setuptools import find_packages, setup

setup(
    name='contracts',
    version='1.0',
    description='A contract management plugin for NetBox',
    author='Marc Lebreuil',
    license='Apache 2.0',
    install_requires=[
        'python-dateutil'
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'netbox-contracts': ["*.html"],
    },
    zip_safe=False,
)