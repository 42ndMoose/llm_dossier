from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path

NUM_HEADING_RE = re.compile(r'^\s*(\d+)\.\s+(.+?)\s*$')
MD_HEADING_RE = re.compile(r'^\s*(#{1,6})\s+(.+?)\s*$')
DIVIDER_RE = re.compile(r'^\s*(?:⸻+|[-_]{3,}|={3,})\s*$')
CLAIM_BLOCK_START_RE = re.compile(r'^\s*(?:[-*]\s*)?\[(?i:claim)\]\s*$')
CLAIM_BLOCK_END_RE = re.compile(r'^\s*\[/(?i:claim)\]\s*$')
CLAIM_LINE_RE = re.compile(r'^\s*(?:[-*]\s*)?(?:\[(?i:claim)\]\s*|(?i:claim)\s*:\s*).+?\s*$')
C_MARKER_RE = re.compile(r'\s*\[(?i:c)\]\s*')
EVIDENCE_HEADER_RE = re.compile(r'^\s*(?i:(evidence|links|sources|verification paths?|verify|citations))\s*:?\s*(?:\(.*\))?\s*$')

DOC_TITLE = "Trump's second term, elite factions, legacy media, and the compliance stack"

@dataclass
class Heading:
    kind: str
    number: str
    level: int
    title: str
    line_index: int
    cut_before: int | None = None


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'section'


def parse_front_matter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}, text
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    if end_idx is None:
        return {}, text
    fm_lines = lines[1:end_idx]
    body = '\n'.join(lines[end_idx + 1:]).lstrip('\n')
    meta: dict = {}
    cur_key: str | None = None
    for raw in fm_lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        m_item = re.match(r'^\s*-\s*(.+?)\s*$', line)
        if m_item and cur_key:
            meta.setdefault(cur_key, [])
            if isinstance(meta[cur_key], list):
                meta[cur_key].append(m_item.group(1).strip('"').strip("'"))
            continue
        m_kv = re.match(r'^\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$', line)
        if m_kv:
            key = m_kv.group(1)
            val = m_kv.group(2)
            cur_key = key
            if val == '':
                meta[key] = []
            else:
                meta[key] = val.strip().strip('"').strip("'")
    return meta, body


def wipe_output_dir(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob('*'):
        if p.is_file() and p.suffix in {'.html', '.json'}:
            p.unlink()


def strip_claims(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []

    def is_boundary(line: str) -> bool:
        s = line.strip()
        return bool(NUM_HEADING_RE.match(s) or MD_HEADING_RE.match(s) or DIVIDER_RE.match(s))

    def is_claim_start(line: str) -> bool:
        return bool(CLAIM_BLOCK_START_RE.match(line) or CLAIM_LINE_RE.match(line) or C_MARKER_RE.search(line))

    i = 0
    skip_after_c = False
    while i < len(lines):
        line = lines[i]

        if CLAIM_BLOCK_START_RE.match(line):
            i += 1
            while i < len(lines) and not CLAIM_BLOCK_END_RE.match(lines[i]):
                i += 1
            if i < len(lines):
                i += 1
            skip_after_c = False
            continue

        if CLAIM_LINE_RE.match(line):
            i += 1
            skip_after_c = False
            continue

        if skip_after_c:
            s = line.strip()
            if not s:
                if out and out[-1].strip():
                    out.append('')
                i += 1
                skip_after_c = False
                continue
            if is_boundary(line) or is_claim_start(line):
                skip_after_c = False
                continue
            i += 1
            continue

        if EVIDENCE_HEADER_RE.match(line):
            i += 1
            while i < len(lines):
                if not lines[i].strip():
                    break
                if is_boundary(lines[i]) or is_claim_start(lines[i]):
                    break
                i += 1
            if i < len(lines) and not lines[i].strip():
                if out and out[-1].strip():
                    out.append('')
                i += 1
            continue

        had_c = bool(C_MARKER_RE.search(line))
        cleaned = C_MARKER_RE.sub(' ', line)
        cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned).rstrip()
        out.append(cleaned)
        if had_c:
            skip_after_c = True
        i += 1

    return '\n'.join(out).strip() + '\n'


def render_index(doc_title: str, toc_entries: list[dict]) -> str:
    html_parts = [
        '<!doctype html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8"/>',
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>',
        f'<title>{escape(doc_title)} - Index</title>',
        '</head>',
        '<body>',
        '<main>',
        f'<h1>{escape(doc_title)}</h1>',
        '<p>This build keeps the sectioned navigation model, but tightens the dossier into a more paper-like structure. Read the section pages through the table of contents instead of loading the whole thing at once.</p>',
        '<p><a href="./toc.json">toc.json</a> | <a href="./claims.html">claims.html</a></p>',
        '<hr/>',
        '<h2>Table of contents</h2>',
    ]

    cur_level = 0
    for e in toc_entries:
        lvl = int(e.get('level', 1))
        title = escape(e.get('title', 'Untitled'))
        number = escape(e.get('number', '') or '')
        url = escape(e['url'])
        while cur_level < lvl:
            html_parts.append('<ul>')
            cur_level += 1
        while cur_level > lvl:
            html_parts.append('</ul>')
            cur_level -= 1
        label = f'{number}. {title}' if number else title
        html_parts.append(f'<li><a href="./{url}">{label}</a></li>')
    while cur_level > 0:
        html_parts.append('</ul>')
        cur_level -= 1

    html_parts += ['</main>', '</body>', '</html>']
    return '\n'.join(html_parts)


def render_page(doc_title: str, page_title: str, body_text: str, meta: dict, prev_url: str | None, next_url: str | None) -> str:
    nav_bits = ['<a href="./index.html">Index</a>']
    if prev_url:
        nav_bits.append(f'<a href="./{escape(prev_url)}">Prev</a>')
    if next_url:
        nav_bits.append(f'<a href="./{escape(next_url)}">Next</a>')
    nav = ' | '.join(nav_bits)
    meta_json = escape(json.dumps(meta, ensure_ascii=False, indent=2))
    return '\n'.join([
        '<!doctype html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8"/>',
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>',
        f'<title>{escape(doc_title)} - {escape(page_title)}</title>',
        '</head>',
        '<body>',
        f'<nav>{nav}</nav>',
        '<main>',
        f'<h1>{escape(page_title)}</h1>',
        f'<script type="application/json" id="section-meta">{meta_json}</script>',
        '<pre style="white-space:pre-wrap;line-height:1.35">',
        escape(body_text),
        '</pre>',
        '</main>',
        '</body>',
        '</html>',
    ])


def build_from_parts(parts_dir: Path, outdir: Path, doc_title: str) -> None:
    wipe_output_dir(outdir)
    items: list[dict] = []
    for p in sorted(parts_dir.glob('*.md')):
        raw = p.read_text(encoding='utf-8')
        meta, body = parse_front_matter(raw)
        sec_id = meta.get('id') or slugify(p.stem)
        order = meta.get('order') or '999999'
        title = meta.get('title') or p.stem
        number = meta.get('number') or ''
        level = int(meta.get('level') or 1)
        url = f'{sec_id}.html'
        meta_norm = {
            'id': sec_id,
            'order': order,
            'number': number,
            'level': level,
            'title': title,
            'keywords': meta.get('keywords', []),
            'summary': meta.get('summary', []),
            'related': meta.get('related', []),
            'url': url,
        }
        items.append({'order': str(order), 'id': str(sec_id), 'meta': meta_norm, 'body': body})
    items.sort(key=lambda x: (x['order'], x['id']))

    for i, it in enumerate(items):
        prev_url = items[i - 1]['meta']['url'] if i > 0 else None
        next_url = items[i + 1]['meta']['url'] if i + 1 < len(items) else None
        m = it['meta']
        page_title = f"{m['number']}. {m['title']}".strip('. ').strip() if m['number'] else m['title']
        clean_body = strip_claims(it['body'])
        html = render_page(doc_title, page_title, clean_body, m, prev_url, next_url)
        (outdir / m['url']).write_text(html, encoding='utf-8')

    toc_entries = [it['meta'] for it in items]
    (outdir / 'index.html').write_text(render_index(doc_title, toc_entries), encoding='utf-8')
    (outdir / 'toc.json').write_text(json.dumps(toc_entries, ensure_ascii=False, indent=2), encoding='utf-8')


def main(src: str, outdir: str) -> None:
    src_path = Path(src)
    out_path = Path(outdir)
    if src_path.is_dir():
        build_from_parts(src_path, out_path, DOC_TITLE)
    else:
        raise SystemExit('This rebuild expects a parts directory as input.')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python tools/split_dossier.py <parts_dir> <output_dir>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
