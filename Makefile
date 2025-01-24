PLUGIN_NAME=netbox_contract
REPO_PATH=/opt/netbox/netbox/netbox-contract
VENV_PY_PATH=/opt/netbox/venv/bin/python3
NETBOX_MANAGE_PATH=/opt/netbox/netbox

##################
##     DOCKER    #
##################
#
## Outside of Devcontainer
#
.PHONY: cleanup ## Clean associated docker resources.
cleanup:
	- docker compose -p netbox-contract_devcontainer rm -fv

##################
#   PLUGIN DEV   #
##################

# in VS Code Devcontianer

.PHONY: precommit ## Run precommit
precommit:
	- pre-commit run --all-files


.PHONY: nbshell ## Run nbshell
nbshell:
	${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py nbshell
	from netbox_contract.models import *

.PHONY: setup ## Copy plugin settings.  Setup NetBox plugin.
setup:
	- sudo ${VENV_PY_PATH} -m pip install --disable-pip-version-check --no-cache-dir -e ${REPO_PATH}

.PHONY: makemigrations ## Run makemigrations
makemigrations:
	-${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py makemigrations

.PHONY: migrate ## Run migrate
migrate:
	-${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py migrate

.PHONY: collectstatic
collectstatic:
	-${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py collectstatic --no-input

.PHONY: runserver ## Start NetBox with runserver
runserver:
	- ${NETBOX_MANAGE_PATH}/manage.py runserver 0.0.0.0:8000 --insecure

.PHONY: start ## Start NetBox
start:
	- cd /opt/netbox/netbox/ && /opt/netbox/docker-entrypoint.sh && /opt/netbox/launch-netbox.sh

.PHONY: export_data ## export data .sql file
export_data:
	- PGPASSWORD=J5brHrAXFLQSif0K pg_dump -h postgres -U netbox netbox > netbox_export_data.sql

.PHONY: all ## Run all PLUGIN DEV targets
all: setup makemigrations migrate collectstatic runserver

.PHONY: rebuild ## Run PLUGIN DEV targets to rebuild
rebuild: setup makemigrations migrate collectstatic runserver

.PHONY: test
test: setup
	${NETBOX_MANAGE_PATH}/manage.py test ${PLUGIN_NAME}

