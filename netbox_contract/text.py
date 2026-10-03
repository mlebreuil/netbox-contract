"""
Text helpers without database access (Constitution VI), shared by the contract type model and data migration 0051
(#309, research D9 and D10).
"""

from django.utils.text import slugify

DESCRIPTION_LENGTH = 200
EMPTY_SLUG = 'contract-type'
ELLIPSIS = '…'


def unique_slug(name, taken):
    """The slug of `name`, made unique against the slugs in `taken` with -2, -3, ..."""
    base = slugify(name)[:96] or EMPTY_SLUG
    slug, number = base, 2
    while slug in taken:
        slug = f'{base}-{number}'
        number += 1
    return slug


def shorten_description(text, limit=DESCRIPTION_LENGTH):
    """
    `text` when it fits in `limit` characters; otherwise its beginning, cut at the last space of the first
    limit - 1 characters (or at limit - 1 when there is none), followed by an ellipsis.
    """
    if len(text) <= limit:
        return text
    head = text[:limit - 1]
    cut = head.rfind(' ')
    if cut > 0:
        head = head[:cut]
    return head.rstrip() + ELLIPSIS


def restored_description(description, comments):
    """
    The full description moved to the comments by migration 0051, or None when `description` was not shortened
    from these comments (used by the reverse migration).
    """
    if comments and len(comments) > DESCRIPTION_LENGTH and shorten_description(comments) == description:
        return comments
    return None


def plan_contract_type_changes(rows, taken):
    """
    What migration 0051 changes on existing contract types, given rows of (pk, name, slug, description) and the slugs
    already used. Returns ({pk: {field: value}}, report lines). Rows that already have a slug and a short description
    are left out, so a second run changes nothing.
    """
    taken = set(taken)
    changes, report = {}, []
    for pk, name, slug, description in rows:
        change = {}
        if not slug:
            change['slug'] = unique_slug(name, taken)
            taken.add(change['slug'])
            if change['slug'] != (slugify(name)[:96] or EMPTY_SLUG):
                report.append(f'contract type {name}: slug {change["slug"]} (the slug of its name was taken)')
        if description and len(description) > DESCRIPTION_LENGTH:
            change['description'] = shorten_description(description)
            change['comments'] = description
            report.append(f'contract type {name}: description shortened, full text moved to comments')
        if change:
            changes[pk] = change
    return changes, report
