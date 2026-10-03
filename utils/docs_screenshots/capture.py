"""
Capture the documentation screenshots from a running NetBox seeded by seed.py (see make_screenshots.sh).

    capture.py --ids ids.json --out ../../docs/img [--base-url http://127.0.0.1:8001] [name ...]

Each screenshot is a region of a page, from the top of its first element to the bottom of its last one, so the crops
follow layout changes. To add a screenshot, add a line to SHOTS and reference docs/img/<name>.png from the docs.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

HEADER = '.page-header'
FIRST_ROW = '.page-body .row >> nth=0'
FIRST_ALERT = '.page-body .alert >> nth=0'
LIST_TABLE = '.tab-pane.active .card >> nth=0'


def panel(title):
    """The detail page panel (card) whose header starts with title."""
    return f'.card:has(> .card-header:text-matches("^\\\\s*{title}"))'


# name: (page, first element, last element); pages are formatted with the ids written by seed.py
SHOTS = {
    'contract': ('/plugins/contracts/contracts/{contract}/', HEADER, FIRST_ROW),
    'contract_linked_objects': ('/plugins/contracts/contracts/{contract}/', FIRST_ALERT, panel('Invoices')),
    'contract_line': ('/plugins/contracts/contract-lines/{contract_line}/', HEADER, FIRST_ROW),
    'invoice': ('/plugins/contracts/invoices/{invoice}/', HEADER, FIRST_ROW),
    'invoice_linked_objects': ('/plugins/contracts/invoices/{invoice}/', FIRST_ALERT, panel('Contracts')),
    'invoice_lines_preview': (
        # 5 hours of remote hands entered, and an amount equal to the total of the lines
        '/plugins/contracts/invoices/add/?contracts={contract}&line-{usage_line}-quantity=5&amount=11515.00',
        '#invoice-lines-preview',
        '#invoice-lines-preview',
    ),
    'invoice_line': ('/plugins/contracts/invoiceline/{invoice_line}/', HEADER, FIRST_ROW),
    'accounting_dimensions': ('/plugins/contracts/accountingdimension/', HEADER, LIST_TABLE),
}
PADDING = 8


def box(page, selector):
    """
    The box of the first element matching selector. A row's box includes the bottom margin of its panels, which
    would bring the top of the next element into the crop: the bottom of an element containing panels (cards) is
    the bottom of its lowest panel.
    """
    locator = page.locator(selector).first
    locator.wait_for(state='visible')
    result = locator.bounding_box()
    cards_bottom = locator.evaluate(
        "e => e.matches('.card') ? null"
        " : Math.max(...[...e.querySelectorAll('.card')].map(c => c.getBoundingClientRect().bottom), -1)"
    )
    if cards_bottom is not None and cards_bottom > 0:
        result['height'] = cards_bottom - result['y']
    return result


def capture(page, base_url, out, name, path, first, last):
    page.goto(base_url + path)
    page.wait_for_load_state('networkidle')
    # A viewport as tall as the page keeps sticky elements (form buttons) at the bottom instead of over the content
    page.set_viewport_size({'width': 1440, 'height': page.evaluate('document.documentElement.scrollHeight')})
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(300)
    top, bottom, content = box(page, first), box(page, last), box(page, '.page-wrapper')
    left = max(min(top['x'], bottom['x']) - PADDING, content['x'])
    right = min(max(top['x'] + top['width'], bottom['x'] + bottom['width']) + PADDING, content['x'] + content['width'])
    y = max(top['y'] - PADDING, content['y'])
    clip = {'x': left, 'y': y, 'width': right - left, 'height': bottom['y'] + bottom['height'] + PADDING - y}
    page.screenshot(path=out / f'{name}.png', clip=clip)
    page.set_viewport_size({'width': 1440, 'height': 900})
    print(f'{name}.png  {int(clip["width"])}x{int(clip["height"])}  {page.title()}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ids', required=True, help='JSON file written by seed.py')
    parser.add_argument('--out', required=True, type=Path, help='output directory (docs/img)')
    parser.add_argument('--base-url', default='http://127.0.0.1:8001')
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', default='admin')
    parser.add_argument('names', nargs='*', help=f'screenshots to take (default: all): {", ".join(SHOTS)}')
    args = parser.parse_args()
    ids = json.loads(Path(args.ids).read_text())
    unknown = set(args.names) - set(SHOTS)
    if unknown:
        parser.error(f'unknown screenshots: {", ".join(sorted(unknown))}')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, color_scheme='dark')
        page.goto(f'{args.base_url}/login/')
        page.fill('input[name=username]', args.user)
        page.fill('input[name=password]', args.password)
        page.click('button[type=submit]')
        page.wait_for_url(lambda url: '/login/' not in url)
        for name in args.names or SHOTS:
            path, first, last = SHOTS[name]
            capture(page, args.base_url, args.out, name, path.format(**ids), first, last)
        browser.close()


if __name__ == '__main__':
    main()
