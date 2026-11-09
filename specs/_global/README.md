# Global specification view

The specifications in `specs/NNN-*/` describe one change each. This directory describes the product **as it is
now**, assembled from all of them and updated by each new feature. Start here to learn what the plugin does; follow
the identifiers (`001-FR-031`) to the specification that explains why.

| Document | Content |
|---|---|
| [CONVENTIONS.md](CONVENTIONS.md) | Identifier scheme, tool, and how features update this directory |
| [registry.md](registry.md) | Generated list of every defined identifier and how often code cites it |
| [behaviours.md](behaviours.md) | Business rules by domain with their identifiers |
| [data-model.md](data-model.md) | Models, fields, constraints, locks, migrations |
| [contracts/rest-api.md](contracts/rest-api.md) | REST API |
| [contracts/graphql.md](contracts/graphql.md) | GraphQL API |
| [contracts/ui.md](contracts/ui.md) | Pages, forms, actions, settings |
| [contracts/routes.md](contracts/routes.md) | Route names and addresses |
| [contracts/operations.md](contracts/operations.md) | Commands, scripts, metadata, CI |

Features so far: 001 contract lines and billing, 002 NetBox 4.6 conventions, 003 NetBox 4.6 plugin features,
004 generic object selector, 005 breadcrumb layouts, 006 GraphQL core extensions, 007 choice descriptions,
008 NetBox 4.7 baseline.
