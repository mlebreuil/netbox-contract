# Developing

## VSCode + Docker + Dev Containers

To develop this plugin further, you can use the included `.devcontainer` configuration. This configuration creates a Docker container that includes a fully working NetBox installation.

By default, the instance will be prepopulated with the latest NetBox demo data and additional data for NetBox Contract.

### Loaded Data
The data is loaded from [netbox-demo-data](https://github.com/netbox-community/netbox-demo-data) and enriched with data for all NetBox Contract models.

### Requirements
- VSCode
- Dev Containers extension (`ms-vscode-remote.remote-containers`)
- Docker Compose

### Getting Started

1. Press `Ctrl+Shift+P` and select "Dev Containers: Open Folder in Container", then choose your netbox-contract folder
2. Start the NetBox instance using: `make all`

Your netbox instance will be served under `0.0.0.0:8000`, so it should now be available under `127.0.0:1:8000`.


## Aliases and Make Commands

All available commands are documented in the `Makefile`.

## Restart from scratch

1. Outside the Docker dev container: `make cleanup` 
2. Restart and open the folder in container

## Generate a new SQL file

Inside the dev container: `make export_data`
