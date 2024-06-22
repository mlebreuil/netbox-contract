# vscode dev environment setup
## Configure the dev environment
### create the dev container

Create a netbox folder
clone your fork of the netbox-contract repository 
Copy the utils/.devcontainer folder to your root directory

Save the workspace definition file to the root of the netbox folder
File > Save workspace as

Press F1
Dev Container: Rebuild container and reopen in container

### initialisze the database

Install database package.  
postgresql python adapter [psycopg](https://www.psycopg.org/docs/install.html)  

```bash
pip install psycopg2
```

Run the initialization script

```bash
python3 netbox-contract/utils/database_init.py
```

## Install Netbox
 
[netbox installtion doc](https://netboxlabs.com/docs/netbox/en/stable/installation/3-netbox/)

### Clone the netbox repository

```bash
mkdir netbox
cd netbox
git clone -b master --depth 1 https://github.com/netbox-community/netbox.git .
```

You do not need to create the Betbox system user

### generate secret key

```
python3 netbox/netbox/generate_secret_key.py
```

update the netbox-contract/utils/netbox-configuration.py with this secret key

### update netbox configuration

```
sudo cp netbox-contract/utils/netbox-configuration.py netbox/netbox/netbox/configuration.py
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

### Install the plugin

For development, install the plugin from the local file system:  

 ```bash
python3 -m pip install -e netbox-contract
```

Update netbox configuration to configure the plugin:

```bash
sudo cp netbox-contract/utils/netbox-configuration-final.py netbox/netbox/netbox/configuration.py
```
run database migrations:

```bash
python3 netbox/netbox/manage.py migrate
```

install pre-commit:  

```bash
cd netbox-contract
python -m pip install pre-commit
pre-commit install
```

Test the installation

```bash
cd ..
python3 netbox/netbox/manage.py runserver
```

## Upgrade Netbox

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

## Model changes

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


