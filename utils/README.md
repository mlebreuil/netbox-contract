# vscode dev environment setup
## Configure the dev environment
### create the dev container

Copy the .devcontainer
File Save workspace as

ctrl + shift + P
Dev Container: Rebuild container and reopen in container

## Install Netbox

Install netbox following the "Option B: Clone the Git Repository":  
[netbox installtion doc](https://github.com/netbox-community/netbox/blob/develop/docs/installation/3-netbox.md)

### Clone Netbox

```bash
mkdir netbox
cd netbox
git clone -b master --depth 1 https://github.com/netbox-community/netbox.git .
```

### initialisze the database

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

### generate secret key

```
python3 netbox/netbox/generate_secret_key.py
```

update the netbox netbox-configuration.py with this secret key

### update netbox configuration

```
cp netbox-configuration.py netbox/netbox/netbox/configuration.py
```

### Run the Upgrade Script

```bash
sudo netbox/upgrade.sh
```

Chnage the ownership of the creaed virtual environment

```bash
cd netbox
sudo chown -R vscode:vscode venv
```

### Create a Super User

```bash
source netbox/venv/bin/activate
python3 netbox/netbox/manage.py createsuperuser
```

### Test installation

```bash
python3 netbox/netbox/manage.py runserver
```

### Upgrade Netbox

Upgrade Netbox:  

```bash
cd netbox
sudo git checkout master
sudo git pull origin master
sudo ./upgrade.sh
```

Change the owner of virtual environment:

```bash
sudo chown -R vscode:vscode venv
```

Reinstall the pluggin from the local filesystem (see below). 

```bash
python -m pip install pre-commit
pre-commit install
```

### Backup and restore the db

```bash
pg_dump --username netbox --password --host db netbox > netbox.sql
```

Restore:  

```bash
psql --host=db --username=postgres --password -c 'drop database netbox'
psql --host=db --username=postgres --password -c 'create database netbox'
psql --host=db --username=postgres --password netbox < netbox.sql
```

## contracts plugin

### Development environment

Convention to adhere to:  
Netbox [Style Guide](https://docs.netbox.dev/en/stable/development/style-guide/)  
Django [Coding style](https://docs.djangoproject.com/en/4.2/internals/contributing/writing-code/coding-style/)  

For this:  
All files will be formated using the [black](https://black.readthedocs.io/en/stable/) auto-formatter.  
Confiiguration is stored in pyproject.toml  

[isort](https://github.com/PyCQA/isort#readme) is used to automate import sorting.  

Linting and PEP8 style enforcement will be done with  [Flake8](https://flake8.pycqa.org/en/latest/) which is a wrapper arround:  
- PyFlakes
- pycodestyle
- Ned Batchelder’s McCabe script
Configuration is maintained in the .flake8 file (no support for pyproject.toml)

The pre-commit Python framework is used to simplify the managment of pre-commit hooks:  
Config is stored in .pre-commit-config.yaml   

```bash
python -m pip install pre-commit
pre-commit install
```

### Model changes

Create the migrations:  

```bash
source netbox/venv/bin/activate
python3 netbox/netbox/manage.py makemigrations netbox_contract --dry-run
python3 netbox/netbox/manage.py makemigrations netbox_contract
```

Apply the migrations:  

```bash
source netbox/venv/bin/activate
python3 netbox/netbox/manage.py migrate
```

### Generating the distribution archives

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

### Update the package in the test pypi repository

```bash
source netbox/venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade twine
python3 -m twine upload --repository testpypi dist/*
```

### Update the package in the pypi repository

Note: This part is now automated with Github Actions.  
Each time a release is created, a new package is created and uploaded to PyPI. 

```bash
source netbox/venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade twine
python3 -m twine upload dist/*
```

### install the pluggin 

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


