from setuptools import find_packages, setup

setup(
    name='contracts',
    version='0.1',
    description='A contract management plugin for NetBox',
    author='Marc Lebreuil',
    license='Apache 2.0',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)