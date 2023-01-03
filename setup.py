from setuptools import find_packages, setup

setup(
    name='netbox-contract',
    version='1.0',
    description='A contract management plugin for NetBox',
    author='Marc Lebreuil',
    license='MIT',
    install_requires=[
        'python-dateutil'
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
)