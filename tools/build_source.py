from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS_DIR = ROOT / 'dossier' / 'parts'
OUT_FILE = ROOT / 'dossier' / 'source.md'
DOC_TITLE = "Trump's second term, elite factions, legacy media, and the compliance stack"


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
                meta[cur_key].append(m_item.group(1))
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


def norm_ws(s: str) -> str:
    return '\n'.join(line.rstrip() for line in s.splitlines()).strip() + '\n'


def truthy(v: object) -> bool:
    return str(v).strip().lower() in {'true', '1', 'yes', 'y', 'on'}


def main() -> None:
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    part_files = sorted([p for p in PARTS_DIR.glob('*.md') if p.is_file()])
    if not part_files:
        raise SystemExit(f'No parts found in {PARTS_DIR}')

    parts: list[dict] = []
    for p in part_files:
        raw = p.read_text(encoding='utf-8')
        meta, body = parse_front_matter(raw)
        if truthy(meta.get('exclude_from_source', False)):
            continue
        body = norm_ws(body)
        if not body.strip():
            continue
        parts.append({
            'path': p,
            'order': str(meta.get('order', '999999')),
            'body': body,
        })

    parts.sort(key=lambda x: (x['order'], x['path'].name))

    chunks: list[str] = [DOC_TITLE.strip() + '\n']
    for idx, item in enumerate(parts):
        p = item['path']
        if idx > 0:
            chunks.append('\n⸻\n\n')
        chunks.append(f'<!-- BEGIN {p.name} -->\n\n')
        chunks.append(item['body'])
        chunks.append(f'\n<!-- END {p.name} -->\n')

    OUT_FILE.write_text(''.join(chunks).strip() + '\n', encoding='utf-8')
    print(f'Wrote {OUT_FILE}')


if __name__ == '__main__':
    main()
