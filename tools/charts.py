"""Chart helpers for the generated guides: plain HTML and CSS, no libraries.

Specs follow the dataviz rules: bars at most 24px thick with 4px rounded data-ends and square
baselines, values at the bar tip, text in text tokens (never the data
colour), a native hover tooltip per mark, and a table view for every chart.
"""
from html import escape

BLUE = '#1f5eff'
# Validated with the dataviz validator (light surface): all six checks pass; three slots are
# under 3:1 against white, so every segmented bar ships with a legend carrying values and a table.
CATEGORICAL = ['#1f5eff', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']


def _table(caption, head, rows):
    th = ''.join(f'<th scope="col">{escape(h)}</th>' for h in head)
    tr = ''.join('<tr>' + ''.join(f'<td>{escape(str(c))}</td>' for c in r) + '</tr>' for r in rows)
    return (f'<details class="chart-table"><summary>Show the numbers</summary>'
            f'<table><caption class="visually-hidden">{escape(caption)}</caption><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></details>')


def hbar(title, items, fmt, note='', ref=None, highlight=None, key=None):
    """Horizontal bars as HTML, so labels stay readable at phone width. items: [(label, value)],
    in the order given. ref: (value, label) for one thin reference rule. highlight: labels drawn in
    brand blue, the rest in a muted step; key names what the blue means (identity never colour alone)."""
    vmax = max([v for _, v in items] + ([ref[0]] if ref else [])) * 1.22  # headroom for the value at the tip
    rule = f'<s style="left:{ref[0] / vmax * 100:.2f}%"></s>' if ref else ''
    rows = []
    for label, v in items:
        col = BLUE if (highlight is None or label in highlight) else '#9db7ff'
        rows.append(f'<li title="{escape(label)}: {escape(fmt(v))}"><span class="hb-l">{escape(label)}</span>'
                    f'<span class="hb-t"><i style="width:{max(v / vmax * 100, .6):.2f}%;background:{col}"></i>'
                    f'<b>{escape(fmt(v))}</b>{rule}</span></li>')
    foot = []
    if ref:
        foot.append(f'<li><i class="hb-key-rule"></i>{escape(ref[1])}</li>')
    if key:
        foot += [f'<li><i style="background:{BLUE}"></i>{escape(key[0])}</li>',
                 f'<li><i style="background:#9db7ff"></i>{escape(key[1])}</li>']
    table = _table(title, ['', 'Value'], [(l, fmt(v)) for l, v in items])
    return (f'<figure class="chart-card"><figcaption><b>{escape(title)}</b>'
            + (f'<span>{escape(note)}</span>' if note else '')
            + f'</figcaption><ul class="hbars" aria-label="{escape(title)}">' + ''.join(rows) + '</ul>'
            + (f'<ul class="seg-legend">{"".join(foot)}</ul>' if foot else '') + f'{table}</figure>')


def segbar(title, parts, fmt, note=''):
    """Tall segmented bar: one whole split into parts. parts: [(label, value)] in fixed order."""
    total = sum(v for _, v in parts)
    blocks, legend = [], []
    for i, (label, v) in enumerate(parts):
        share = v / total * 100
        col = CATEGORICAL[i]
        ink = '#fff' if i == 0 else '#0f172a'  # white on the brand blue, near-black on the light hues
        text = f'{round(share)}%' if share >= 9 else ''
        blocks.append(f'<span class="seg" style="width:{share:.2f}%;background:{col};color:{ink}" '
                      f'title="{escape(label)}: {escape(fmt(v))} ({share:.0f}%)">{text}</span>')
        legend.append(f'<li><i style="background:{col}"></i>{escape(label)} <b>{escape(fmt(v))}</b></li>')
    table = _table(title, ['', 'Per month', 'Share'], [(l, fmt(v), f'{v / total * 100:.0f}%') for l, v in parts]
                   + [('Total', fmt(total), '100%')])
    return (f'<figure class="chart-card"><figcaption><b>{escape(title)}</b>'
            + (f'<span>{escape(note)}</span>' if note else '')
            + f'</figcaption><div class="segbar" role="img" aria-label="{escape(title)}: total {escape(fmt(total))}">'
            + ''.join(blocks) + '</div><ul class="seg-legend">' + ''.join(legend) + f'</ul>{table}</figure>')


def stats(items):
    """Stat tiles: [(value, label)]."""
    return '<ul class="stats guide-stats">' + ''.join(
        f'<li><strong>{escape(v)}</strong><span>{escape(l)}</span></li>' for v, l in items) + '</ul>'


if __name__ == '__main__':
    # Smallest check that the shapes stay sane: widths add up and labels survive escaping.
    out = segbar('Test', [('Rent', 600), ('Food & drink', 300), ('Other', 100)], lambda v: f'€{v}')
    assert out.count('class="seg"') == 3 and 'Food &amp; drink' in out
    widths = [float(w) for w in __import__('re').findall(r'width:([\d.]+)%', out)]
    assert abs(sum(widths) - 100) < 0.1, widths
    bar = hbar('T', [('A', 10), ('B', 5)], str, ref=(8, 'ref'))
    assert bar.count('<li title=') == 2 and bar.count('<s style') == 2 and 'Show the numbers' in bar
    print('charts ok')
