PLUGIN_NAME=netbox_contract
REPO_PATH=/opt/netbox/netbox/netbox-contract
VENV_PY_PATH=/opt/netbox/venv/bin/python3
NETBOX_MANAGE_PATH=/opt/netbox/netbox
NETBOX_INITIALIZER_PATH=${NETBOX_MANAGE_PATH}/netbox_initializers/
VERFILE=./version.py

.PHONY: help ## Display help message
help:
	@grep -E '^[0-9a-zA-Z_-]+\.*[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

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

.PHONY: nbshell ## Run nbshell
nbshell:
	${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py nbshell
	from netbox_contract.models import *

.PHONY: setup ## Copy plugin settings.  Setup NetBox plugin.
setup:
	- sudo ${VENV_PY_PATH} -m pip install --disable-pip-version-check --no-cache-dir -e ${REPO_PATH}

.PHONY: makemigrations ## Run makemigrations
makemigrations:
	-${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py makemigrations --name ${PLUGIN_NAME}

.PHONY: migrate ## Run migrate
migrate:
	-${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py migrate

.PHONY: collectstatic
collectstatic:
	-${VENV_PY_PATH} ${NETBOX_MANAGE_PATH}/manage.py collectstatic --no-input

.PHONY: dev_start ## Start NetBox with runserver
dev_start:
	- /opt/netbox/netbox/manage.py runserver 0.0.0.0:8000 --insecure

.PHONY: start ## Start NetBox
start:
	- cd /opt/netbox/netbox/ && /opt/netbox/docker-entrypoint.sh && /opt/netbox/launch-netbox.sh

.PHONY: export_data # export data .sql file
export_data:
	- PGPASSWORD=J5brHrAXFLQSif0K pg_dump -h postgres -U netbox netbox > netbox_$(date +%Y-%m-%d).sql

.PHONY: all ## Run all PLUGIN DEV targets
all: setup makemigrations migrate collectstatic dev_start

.PHONY: rebuild ## Run PLUGIN DEV targets to rebuild
rebuild: setup makemigrations migrate collectstatic dev_start

.PHONY: test
test: setup
	${NETBOX_MANAGE_PATH}/manage.py makemigrations ${PLUGIN_NAME} --check
	coverage run --source "netbox_contract" ${NETBOX_MANAGE_PATH}/manage.py test ${PLUGIN_NAME} -v 2

# .PHONY: coverage_report
# coverage_report:
# 	coverage report

# .PHONY: test_coverage
# test_coverage: test coverage_report

