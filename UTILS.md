# Utils

## Generating the distribution archives

Note: This part is now automated with Github Actions.  
Each time a release is created, a new package is created.

Make sure the package version is incremented in the following files.  
- pyproject.toml  
- src/netbox_contract/__init__.py  

```bash
source netbox/venv/bin/activate
cd netbox-contract
python3 -m pip install --upgrade build
python3 -m build
```

## Update the package in the test pypi repository


```bash
source netbox/venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade twine
python3 -m twine upload --repository testpypi dist/*
```

## Update the package in the pypi repository

Note: This part is now automated with Github Actions.  
Each time a release is created, a new package is created and uploaded to PyPI. 

```bash
source netbox/venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade twine
python3 -m twine upload dist/*
```

## install the pluggin 

For development install from local file system with the "editable" option:   

git clone

```bash
source netbox/venv/bin/activate
python3 -m pip uninstall netbox-contract
git clone https://github.com/mlebreuil/netbox-contract.git
python3 -m pip install -e netbox-contract
```

from the test respository:  

```bash
source netbox/venv/bin/activate
python3 -m pip uninstall netbox-contract
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps netbox-contract
```

From the production repository:

```bash
source netbox/venv/bin/activate
python3 -m pip uninstall netbox-contract
python3 -m pip install netbox-contract
```

Update netbox configuration

```python
# configuration.py
PLUGINS = [
    'netbox_contract',
]
```

update the database

```bash
source netbox/venv/bin/activate
python netbox/netbox/manage.py migrate
```

## initialisze the database

Install database package.  
postgresql python adapter [psycopg](https://www.psycopg.org/docs/install.html)  

```bash
pip install psycopg2
```

Run the initialization script

```bash
cd ..
python3 database_init.py
```

## Backup and restore the db

```bash
pg_dump --username netbox --password --host db netbox > netbox.sql
```

Restore:  

```bash
psql --host=db --username=postgres --password -c 'drop database netbox'
psql --host=db --username=postgres --password -c 'create database netbox'
psql --host=db --username=postgres --password netbox < netbox.sql
```