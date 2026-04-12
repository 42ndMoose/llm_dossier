from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

BEGIN_PART_RE = re.compile(r'^\s*<!--\s*BEGIN\s+(.+?)\s*-->\s*$')
CLAIM_LINE_RE = re.compile(r'^\s*(?:[-*]\s*)?(?:\[(?i:claim)\]\s*|(?i:claim)\s*:\s*)(.+?)\s*$')
CLAIM_BLOCK_START_RE = re.compile(r'^\s*(?:[-*]\s*)?\[(?i:claim)\]\s*$')
CLAIM_BLOCK_END_RE = re.compile(r'^\s*\[/(?i:claim)\]\s*$')
C_SUFFIX_RE = re.compile(r'^\s*(.+?)\s*\[c\]\s*$', re.IGNORECASE)
URL_RE = re.compile(r'https?://[^\s)>\]]+')
META_LINE_RE = re.compile(r'^\s*(date|title|tags|note)\s*:\s*(.+?)\s*$', re.IGNORECASE)
EVIDENCE_LABEL_RE = re.compile(r'^\s*(evidence|links|sources|verification paths?|verify|citations)\s*:?\s*(?:\(.*\))?\s*$', re.IGNORECASE)
ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _strip_wrapping_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1].strip()
    return s


def _ensure_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [_strip_wrapping_quotes(str(x)) for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if s in ('', '[]'):
            return []
        return [_strip_wrapping_quotes(s)]
    s = str(v).strip()
    return [s] if s else []


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
                meta[cur_key].append(_strip_wrapping_quotes(m_item.group(1)))
            continue
        m_kv = re.match(r'^\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$', line)
        if m_kv:
            key = m_kv.group(1)
            val = m_kv.group(2)
            cur_key = key
            meta[key] = [] if val == '' else _strip_wrapping_quotes(val)
    return meta, body


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'section'


def load_parts_index(parts_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not parts_dir.exists():
        return out
    for p in parts_dir.glob('*.md'):
        raw = p.read_text(encoding='utf-8')
        meta, _ = parse_front_matter(raw)
        sec_id = meta.get('id') or slugify(p.stem)
        out[p.name] = {
            'id': str(sec_id),
            'order': str(meta.get('order') or '999999'),
            'number': str(meta.get('number') or ''),
            'level': int(meta.get('level') or 1),
            'title': str(meta.get('title') or p.stem),
            'keywords': _ensure_list(meta.get('keywords')),
            'summary': _ensure_list(meta.get('summary')),
            'related': _ensure_list(meta.get('related')),
            'url': f'{sec_id}.html',
        }
    return out


def claim_id(section_id: str, idx: int) -> str:
    return f'C-{section_id}-{idx:03d}'


def pick_doc_title(lines: list[str]) -> str:
    for ln in lines:
        if ln.strip():
            return ln.strip().lstrip('#').strip() or 'Dossier'
    return 'Dossier'


def _section_fields(current_part_meta: dict | None) -> tuple[str, str, str]:
    if current_part_meta:
        sec_id = current_part_meta['id']
        sec_label = f"{current_part_meta['number']}. {current_part_meta['title']}".strip() if current_part_meta.get('number') else current_part_meta['title']
        return sec_id, sec_label, current_part_meta['url']
    return 'no-part', 'No part', ''


def _unique_urls(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in URL_RE.findall(text or ''):
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def parse_event_meta(evidence_text: str) -> tuple[dict, str]:
    meta: dict = {}
    cleaned: list[str] = []
    for raw in (evidence_text or '').splitlines():
        line = raw.rstrip()
        m = META_LINE_RE.match(line)
        if m:
            k = m.group(1).lower()
            v = m.group(2).strip()
            if k == 'tags':
                meta['tags'] = [t.strip() for t in v.split(',') if t.strip()]
            elif k == 'date':
                if ISO_DATE_RE.match(v):
                    meta['date'] = v
                else:
                    meta['date_raw'] = v
            elif k == 'title':
                meta['title'] = v
            elif k == 'note':
                meta['note'] = v
            continue
        if EVIDENCE_LABEL_RE.match(line):
            continue
        cleaned.append(line)
    return meta, '\n'.join(cleaned).strip()


def render_claims_html(doc_title: str, claims: list[dict]) -> str:
    rows = []
    for c in claims:
        cid = escape(c['id'])
        txt = escape(c['text'])
        sec_label = escape(c.get('section_label', ''))
        url = escape(c.get('url', ''))
        line = c.get('line')
        where = sec_label
        if url:
            where = f'<a href="./{url}">{where}</a>'
        if line is not None:
            where += f" <span style='opacity:.7'>(line {int(line)})</span>"
        links_html = ' '.join([f'<a href="{escape(u)}" rel="noreferrer noopener">{escape(u)}</a>' for u in c.get('links', [])])
        date = escape((c.get('date') or c.get('date_raw') or '').strip())
        title = escape((c.get('title') or '').strip())
        tags = escape(', '.join(c.get('tags') or []))
        evc = int(c.get('evidence_count', 0))
        rows.append(
            f"<tr id='{cid}'><td style='white-space:nowrap'><a href='./claims.html#{cid}'>{cid}</a></td><td>{txt}</td><td style='white-space:nowrap'>{where}</td><td style='white-space:nowrap'>{date}</td><td>{title}</td><td style='white-space:nowrap'>{tags}</td><td style='text-align:right;white-space:nowrap'>{evc}</td><td>{links_html}</td></tr>"
        )
    body = "<p>No claims found yet.</p>" if not rows else (
        "<table border='1' cellspacing='0' cellpadding='6' style='border-collapse:collapse;width:100%'><thead><tr><th>ID</th><th>Claim</th><th>Section</th><th>Date</th><th>Title</th><th>Tags</th><th>Evidence</th><th>Links</th></tr></thead><tbody>" + '\n'.join(rows) + '</tbody></table>'
    )
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/><title>{escape(doc_title)} - Claims Ledger</title></head><body><nav><a href='./index.html'>Index</a></nav><main><h1>Claims Ledger</h1><p>Internal [C] markers are build scaffolding. They do not appear on the public section pages.</p><ul><li><a href='./claims.json'>claims.json</a></li><li><a href='./claims.min.json'>claims.min.json</a></li></ul>{body}</main></body></html>"


def main(src: str, outdir: str) -> None:
    src_path = Path(src)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    text = src_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    doc_title = pick_doc_title(lines)
    parts_index = load_parts_index(src_path.parent / 'parts')
    claims: list[dict] = []
    claims_min: list[dict] = []
    section_counts: dict[str, int] = {}
    current_part_meta: dict | None = None

    def push_claim(claim_text: str, evidence_text: str, line_no: int) -> None:
        sec_id, sec_label, url = _section_fields(current_part_meta)
        section_counts.setdefault(sec_id, 0)
        section_counts[sec_id] += 1
        cid = claim_id(sec_id, section_counts[sec_id])
        event_meta, cleaned_evidence = parse_event_meta(evidence_text)
        links = _unique_urls(evidence_text if evidence_text else claim_text)
        evidence_count = len(links)
        claims.append({
            'id': cid,
            'text': claim_text.strip(),
            'evidence': cleaned_evidence.strip(),
            'evidence_count': evidence_count,
            'links': links,
            'section_id': sec_id,
            'section_label': sec_label,
            'url': url,
            'line': line_no,
            'date': event_meta.get('date', ''),
            'date_raw': event_meta.get('date_raw', ''),
            'title': event_meta.get('title', ''),
            'tags': event_meta.get('tags', []),
            'note': event_meta.get('note', ''),
        })
        claims_min.append({'id': cid, 'u': url, 't': ' '.join(claim_text.split()), 'ec': evidence_count, 'd': event_meta.get('date', ''), 'ti': event_meta.get('title', ''), 'tg': event_meta.get('tags', [])})

    i = 0
    while i < len(lines):
        line = lines[i]
        m_begin = BEGIN_PART_RE.match(line)
        if m_begin:
            current_part_meta = parts_index.get(m_begin.group(1).strip())
            i += 1
            continue
        if CLAIM_BLOCK_START_RE.match(line):
            start = i + 1
            block_lines = []
            i += 1
            while i < len(lines) and not CLAIM_BLOCK_END_RE.match(lines[i]):
                block_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            claim_text = '\n'.join(block_lines).strip()
            if claim_text:
                push_claim(claim_text, claim_text, start)
            continue
        m_c = C_SUFFIX_RE.match(line)
        if m_c:
            start = i + 1
            claim_text = m_c.group(1).strip()
            evidence_lines = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == '':
                    break
                if CLAIM_BLOCK_START_RE.match(nxt) or CLAIM_LINE_RE.match(nxt) or C_SUFFIX_RE.match(nxt):
                    break
                evidence_lines.append(nxt.rstrip())
                i += 1
            if i < len(lines) and lines[i].strip() == '':
                i += 1
            push_claim(claim_text, '\n'.join(evidence_lines).strip(), start)
            continue
        m_line = CLAIM_LINE_RE.match(line)
        if m_line:
            push_claim(m_line.group(1).strip(), '', i + 1)
            i += 1
            continue
        i += 1

    (out / 'claims.json').write_text(json.dumps(claims, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'claims.min.json').write_text(json.dumps(claims_min, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (out / 'claims.html').write_text(render_claims_html(doc_title, claims), encoding='utf-8')
    print(f'Wrote {len(claims)} claims')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python tools/build_claims.py <source.md> <output_dir>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
