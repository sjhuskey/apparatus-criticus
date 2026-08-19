#!/usr/bin/env python3
"""
POC: Extract TEI <app> elements from poem 1, lines 1–20 into "claim" JSON files.

Usage:
  python tei_apps_to_claims.py path/to/giarratano.xml outdir/

Dependencies:
  pip install lxml
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from lxml import etree


NS = {"tei": "http://www.tei-c.org/ns/1.0"}


@dataclass
class Context:
    poem: Optional[str] = None  # e.g., "1"
    line: Optional[str] = None  # e.g., "12"
    app_local_id: str = ""  # deterministic local id for app
    locator: str = ""  # human-readable locator e.g. "Ecl.1.12"


def normalize_sigla_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    # Split on whitespace; strip leading '#' from pointers.
    parts = [p.strip() for p in value.split() if p.strip()]
    parts = [p[1:] if p.startswith("#") else p for p in parts]
    return parts


def is_omission_reading(rdg_el) -> bool:
    # Explicit TEI omission marker
    gaps = rdg_el.xpath(".//tei:gap[@reason='omitted']", namespaces=NS)
    if gaps:
        return True
    # Fallback: no text content at all
    txt = extract_text(rdg_el)
    return txt == ""


def extract_text(el: etree._Element) -> str:
    # Concatenate text content (including inline nodes) without tags.
    return " ".join("".join(el.itertext()).split()).strip()


def safe_slug(s: str) -> str:
    s = s.strip()
    # Normalize whitespace
    s = re.sub(r"\s+", "-", s)

    # Keep ASCII-ish set first
    cleaned = re.sub(r"[^A-Za-z0-9._:-]+", "", s)
    if cleaned:
        return cleaned

    # Fallback for non-ASCII sigla (e.g., Greek letters): use codepoints
    # Example: "φ" -> "u03c6", "χ" -> "u03c7"
    cps = "-".join(f"u{ord(ch):04x}" for ch in s if ch.strip())
    return cps or "unknown"


def find_nearest_line(el: etree._Element) -> Optional[etree._Element]:
    # Try nearest ancestor line, then preceding line.
    line = el.xpath("ancestor::tei:l[1]", namespaces=NS)
    if line:
        return line[0]
    prev = el.xpath("preceding::tei:l[1]", namespaces=NS)
    return prev[0] if prev else None


def find_poem_div(el: etree._Element) -> Optional[etree._Element]:
    # Try common patterns.
    for xp in [
        "ancestor::tei:div[@type='poem'][1]",
        "ancestor::tei:div[@subtype='poem'][1]",
        "ancestor::tei:div[@type='eclogue'][1]",
        "ancestor::tei:div[@subtype='eclogue'][1]",
        "ancestor::tei:div[1]",
    ]:
        res = el.xpath(xp, namespaces=NS)
        if res:
            return res[0]
    return None


def compute_context(app: etree._Element, app_index_within_line: int) -> Context:
    line_el = find_nearest_line(app)
    line_n = None
    if line_el is not None:
        line_n = line_el.get("n")

    poem_el = app.xpath(
        "ancestor::tei:div[@type='textpart' and @subtype='poem'][1]",
        namespaces=NS
    )
    poem_el = poem_el[0] if poem_el else None

    poem_n = poem_el.get("n") if poem_el is not None else None
    poem_xmlid = poem_el.get("{http://www.w3.org/XML/1998/namespace}id") if poem_el is not None else None

    # Human-readable locator
    if poem_n and line_n:
        locator = f"{poem_n}.{line_n}"           # e.g. "1.12"
    elif line_n:
        locator = f"line {line_n}"
    else:
        locator = "unknown-location"

    # Deterministic app id
    xmlid = app.get("{http://www.w3.org/XML/1998/namespace}id")
    if xmlid:
        app_local = xmlid
    else:
        p = poem_xmlid or (f"poem{poem_n}" if poem_n else "poemx")
        l = f"l{line_n}" if line_n else "lx"
        app_local = f"{p}-{l}-app{app_index_within_line:02d}"  # poem1-l12-app03

    return Context(poem=poem_n, line=line_n, app_local_id=app_local, locator=locator)


def evidence_for_agent(ev: list[dict], agent: dict) -> list[dict]:
    """
    For per-agent claims:
      - Witness agents keep only their own witness_support; drop printed_source_support.
      - Printed-source agents keep only their own printed_source_support; drop witness_support.
      - Always keep taxonomy_tags.
    """
    out: list[dict] = []
    is_witness = agent["id"].startswith("MS_")
    is_printed = agent["id"].startswith("ED_")

    witness_siglum = None
    if is_witness:
        # agent name looks like "Witness G" or "Witness φ"
        witness_siglum = agent["name"].replace("Witness ", "")

    for item in ev:
        t = item.get("type")
        if t == "taxonomy_tags":
            out.append(item)
        elif t == "witness_support":
            if is_witness and witness_siglum is not None:
                out.append({"type": "witness_support", "witnesses": [witness_siglum]})
            # else: drop
        elif t == "printed_source_support":
            if is_printed:
                out.append(
                    {"type": "printed_source_support", "sources": [agent["name"]]}
                )
            # else: drop
        else:
            # keep anything else you might add later
            out.append(item)

    return out


def agent_for_witness(siglum: str) -> dict:
    # siglum like "N" or "μ"
    return {"id": f"MS_{safe_slug(siglum)}", "name": f"Witness {siglum}"}


def agent_for_printed_source(token: str) -> dict:
    # token like "Schenkl", "Heins.", "edd.", "p"
    # Keep raw token as name; make stable-ish id
    tid = safe_slug(token).upper()
    return {"id": f"ED_{tid}", "name": token}


def provenance_block(ctx: Context) -> dict:
    return {
        "derived_from": {
            "agent": {"id": "A_GIARRATANO", "name": "Giarratano, Cesar"},
            "source": {
                "id": "SRC_GIARRATANO_TEI",
                "citation": "Giarratano (TEI-encoded apparatus)",
            },
            "tei_app": ctx.app_local_id,
            "locator": ctx.locator,
        }
    }


def make_claim_id(base: str) -> str:
    # Keep filenames stable + readable.
    return "clm-" + safe_slug(base).lower()


def claim_common(
    ctx: Context, work_id: str, edition_id: str, edition_citation: str
) -> Dict[str, Any]:
    return {
        "target": {
            "work": {"id": work_id},
            "passage": {
                "fallback": ctx.locator,
                "local": ctx.app_local_id,
            },
        },
        "agent": {
            # For POC: you can refine these IDs later.
            "id": "A_GIARRATANO",
            "name": "Giarratano, Cesar",
        },
        "source": {
            "id": edition_id,
            "citation": edition_citation,
            "locator": ctx.locator,
            "tei_app": ctx.app_local_id,
        },
        "created": "2026-01-13",
        "updated": "2026-01-13",
    }


def emit_claims_for_reading(
    *,
    out_dir: Path,
    ctx: Context,
    work_id: str,
    edition_id: str,
    edition_citation: str,
    claim_type: str,
    reading_value,
    reading_note: str | None,
    agents: list[dict],
    evidence: list[dict],
    base_id: str,
    per_agent_evidence: bool = False,
) -> int:
    written = 0
    for a in agents:
        ev = evidence_for_agent(evidence, a)
        if per_agent_evidence:
            if a["id"].startswith("MS_"):
                # witness siglum is the last bit after MS_
                sig = a["name"].replace("Witness ", "")
                ev = evidence_for_agent(evidence, a)
            elif a["id"].startswith("ED_"):
                ev = evidence_for_agent(evidence, a)

        claim_id = make_claim_id(f"{base_id}-{a['id']}")
        obj = {
            "id": claim_id,
            "type": claim_type,
            **claim_common(ctx, work_id, edition_id, edition_citation),
            "agent": a,
            "assertion": {"reading": reading_value, "note": reading_note},
            "evidence": ev,
            "relations": [],
            "provenance": provenance_block(ctx),
        }
        write_json(out_dir / f"{claim_id}.json", obj)
        written += 1
    return written


def add_evidence_from_attrs(
    el: etree._Element, keep_ana: bool = True
) -> List[Dict[str, Any]]:
    ev: List[Dict[str, Any]] = []
    wits = normalize_sigla_list(el.get("wit"))
    if wits:
        ev.append({"type": "witness_support", "witnesses": wits})

    srcs = normalize_sigla_list(el.get("source"))
    if srcs:
        ev.append({"type": "printed_source_support", "sources": srcs})

    if keep_ana:
        tags = normalize_sigla_list(el.get("ana"))
        # @ana often looks like "#lexical #morphological"
        if tags:
            ev.append({"type": "taxonomy_tags", "tags": tags})

    return ev


def extract_apps_for_poem_lines(tree: etree._ElementTree, poem_n: str, line_min: int, line_max: int):
    apps = []
    poem_divs = tree.xpath(
        f"//tei:div[@type='textpart' and @subtype='poem' and @n='{poem_n}']",
        namespaces=NS
    )
    if not poem_divs:
        return apps

    scope = poem_divs[0]
    for line_no in range(line_min, line_max + 1):
        for line_el in scope.xpath(f".//tei:l[@n='{line_no}']", namespaces=NS):
            for idx, app in enumerate(line_el.xpath(".//tei:app", namespaces=NS), start=1):
                ctx = compute_context(app, idx)
                apps.append((app, ctx))
    return apps


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python tei_apps_to_claims.py input.xml outdir/")
        return 2

    in_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    # POC config (edit these as needed)
    WORK_ID = "W_CALPURNIUS_POC"  # replace with your DLL work ID if you have it
    EDITION_ID = "SRC_GIARRATANO_TEI"
    EDITION_CITATION = "Giarratano (TEI-encoded apparatus), Calpurnius Siculus"
    KEEP_ANA = True

    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    tree = etree.parse(str(in_path), parser)

    apps = extract_apps_for_poem_lines(tree, poem_n="1", line_min=1, line_max=20)

    if not apps:
        print(
            "No <app> elements found in poem 1, lines 1–20 using the default assumptions."
        )
        print(
            "That likely means your TEI structure differs (e.g., no <l n='...'>, poem div not @n='1')."
        )
        print(
            "If you paste 20–30 lines of surrounding TEI (div/head/l structure), I can tailor the XPath."
        )
        return 1

    count = 0
    for app, ctx in apps:
        # --- Lemma ---
        lem = app.xpath("./tei:lem[1]", namespaces=NS)
        if lem:
            lem_el = lem[0]
            lem_text = extract_text(lem_el)

            wits = normalize_sigla_list(lem_el.get("wit"))
            srcs = normalize_sigla_list(lem_el.get("source"))

            # Lemma may be empty (<lem/>) meaning "no lemma" (addition site)
            if lem_text == "":
                lem_reading = None
                lem_note = "No lemma (<lem/>)."
            else:
                lem_reading = lem_text
                lem_note = "Lemma."

            ev = add_evidence_from_attrs(lem_el, keep_ana=False)

            if wits:
                count += emit_claims_for_reading(
                    out_dir=out_dir,
                    ctx=ctx,
                    work_id=WORK_ID,
                    edition_id=EDITION_ID,
                    edition_citation=EDITION_CITATION,
                    claim_type="attests_reading",
                    reading_value=lem_reading,
                    reading_note=lem_note,
                    agents=[agent_for_witness(w) for w in wits],
                    evidence=ev,
                    base_id=f"{ctx.app_local_id}-lem",
                    per_agent_evidence=True,
                )

            if srcs:
                count += emit_claims_for_reading(
                    out_dir=out_dir,
                    ctx=ctx,
                    work_id=WORK_ID,
                    edition_id=EDITION_ID,
                    edition_citation=EDITION_CITATION,
                    claim_type="adopts_reading",
                    reading_value=lem_reading,
                    reading_note=lem_note,
                    agents=[agent_for_printed_source(s) for s in srcs],
                    evidence=ev,
                    base_id=f"{ctx.app_local_id}-lem",
                    per_agent_evidence=True,
                )

            if not wits and not srcs:
                count += emit_claims_for_reading(
                    out_dir=out_dir,
                    ctx=ctx,
                    work_id=WORK_ID,
                    edition_id=EDITION_ID,
                    edition_citation=EDITION_CITATION,
                    claim_type="adopts_reading",
                    reading_value=lem_reading,
                    reading_note=lem_note,
                    agents=[{"id": "A_GIARRATANO", "name": "Giarratano, Cesar"}],
                    evidence=ev,
                    base_id=f"{ctx.app_local_id}-lem",
                    per_agent_evidence=True,
                )

        # --- Readings ---
        rdgs = app.xpath("./tei:rdg", namespaces=NS)
        for i, rdg_el in enumerate(rdgs, start=1):
            wits = normalize_sigla_list(rdg_el.get("wit"))
            srcs = normalize_sigla_list(rdg_el.get("source"))
            ev = add_evidence_from_attrs(rdg_el, keep_ana=True)

            if is_omission_reading(rdg_el):
                rdg_reading = None
                rdg_note = "om."
            else:
                rdg_reading = extract_text(rdg_el)
                rdg_note = None

            if wits:
                count += emit_claims_for_reading(
                    out_dir=out_dir,
                    ctx=ctx,
                    work_id=WORK_ID,
                    edition_id=EDITION_ID,
                    edition_citation=EDITION_CITATION,
                    claim_type="attests_reading",
                    reading_value=rdg_reading,
                    reading_note=rdg_note,
                    agents=[agent_for_witness(w) for w in wits],
                    evidence=ev,
                    base_id=f"{ctx.app_local_id}-rdg{i:02d}",
                )

            if srcs:
                count += emit_claims_for_reading(
                    out_dir=out_dir,
                    ctx=ctx,
                    work_id=WORK_ID,
                    edition_id=EDITION_ID,
                    edition_citation=EDITION_CITATION,
                    claim_type="adopts_reading",
                    reading_value=rdg_reading,
                    reading_note=rdg_note,
                    agents=[agent_for_printed_source(s) for s in srcs],
                    evidence=ev,
                    base_id=f"{ctx.app_local_id}-rdg{i:02d}",
                    per_agent_evidence=True,
                )

            if not wits and not srcs:
                count += emit_claims_for_reading(
                    out_dir=out_dir,
                    ctx=ctx,
                    work_id=WORK_ID,
                    edition_id=EDITION_ID,
                    edition_citation=EDITION_CITATION,
                    claim_type="reports_variant",
                    reading_value=rdg_reading,
                    reading_note=rdg_note,
                    agents=[{"id": "A_GIARRATANO", "name": "Giarratano, Cesar"}],
                    evidence=ev,
                    base_id=f"{ctx.app_local_id}-rdg{i:02d}",
                    per_agent_evidence=True,
                )

    print(f"Wrote {count} claim files to {out_dir}/ from {len(apps)} <app> elements.")
    return 0

    print(f"Wrote {count} claim files to {out_dir}/ from {len(apps)} <app> elements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
