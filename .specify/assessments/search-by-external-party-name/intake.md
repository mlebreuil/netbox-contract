# Idea Intake: Search contracts by external party name

- **Slug**: search-by-external-party-name
- **Created**: 2026-11-11
- **Source**: https://github.com/mlebreuil/netbox-contract/issues/333 (policy branch: allowlisted, fetched with the container's `gh`)
- **Type**: improvement

## Idea (as captured)

Issue #333 "Search contracts by external party name" (open, unlabeled, unassigned; plugin v2.6.0, NetBox v4.7.0; feature type "New functionality"):

> Today the contract list quick search and NetBox's global search do not match the name of a contract's external party. The party can only be filtered by ID (service_provider_id, provider_id). The cause is that external_party_object is a generic foreign key (content type + ID), which cannot be searched through a normal join. The only party types are service providers and circuit providers.
>
> Proposal:
>
> 1. Contract list quick search: also match contracts whose external party is a service provider or a circuit provider whose name contains the search text. This is one subquery per party type, combined with the content type, added to the existing conditions. The existing Active-only behaviour of the quick search is unchanged.
> 2. Filter by party name: optionally add a filter on the contract list, REST API and GraphQL, next to the existing ID filters.
> 3. Global search: decide whether to index the party name on contracts. NetBox re-indexes an object only when it is saved, so renaming a provider would leave its contracts' index entries stale. This part may be left out or handled separately.
>
> Use case: Users remember the supplier's name, not its database ID.

**Scope chosen by the maintainer for this work: proposals 1 and 2 only.** Proposal 3 (global search indexing) is out of scope.

## Restated

Let users find contracts by typing the name of the external party (service provider or circuit provider) in the contract list quick search, and add a party-name filter on the contract list, REST API and GraphQL, alongside the existing ID filters.

## Origin & Context

- **Raised by**: the issue author (identity not recorded here) [NEEDS CLARIFICATION: is this the maintainer or an outside user?]
- **Trigger**: users remember supplier names, not database IDs.

## First-Glance Unknowns

- [NEEDS CLARIFICATION: filter semantics: exact, contains, or the lookup modifiers (`__ic`, `__n`, ...) that NetBox filter forms offer?]
- [NEEDS CLARIFICATION: one filter for both party types, or one per type (service provider name, circuit provider name)?]
- [NEEDS CLARIFICATION: should the filter name be consistent with the existing `service_provider_id` / `provider_id` filters, and appear in the filter form?]
- [NEEDS CLARIFICATION: does the quick search also need to match other provider fields (slug, account), or the name only?]
- [NEEDS CLARIFICATION: "Active-only behaviour of the quick search is unchanged": what exactly does the current quick search restrict, and does the new match respect it?]
- [NEEDS CLARIFICATION: query-count baseline (`tests/query_counts.json`) impact of the added subqueries on the list view.]
- [NEEDS CLARIFICATION: is a deprecated or removed party type possible (generic key pointing to a deleted object)?]
