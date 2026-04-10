from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PPTX = ROOT / "PJTL Update 2_23_2026.pptx"
OUTPUT_PPTX = ROOT / "deliverables" / "phase-0-progress.pptx"

SLIDE_WIDTH = 9_144_000
SLIDE_HEIGHT = 5_143_500

ACCENT = "0F766E"
TEXT = "111827"
SUBTEXT = "4B5563"
MUTED = "6B7280"
PILL_FILL = "D1FAE5"
PILL_TEXT = "065F46"

SLIDES = [
    {
        "title": "Ride YourWay Phase 0 Progress",
        "subtitle": "Scope, authority, confidence, and blocker handling frozen on April 15, 2026",
        "body": [
            "Status: Phase 0 completed",
            "4 of 4 Phase 0 subtasks closed",
            "Result: build work can start without reopening the scope debate",
        ],
        "footer": "Phase 0 completed | Scope freeze and governance lock",
        "pill": "PHASE 0 COMPLETE",
    },
    {
        "title": "Phase 0 By The Numbers",
        "subtitle": "The point of this phase was to lock execution rules before touching the analytical build",
        "body": [
            "4 subtasks completed: delivery contract, authority precedence, confidence ladder, scope-trim rulebook",
            "6 mandatory MVP outcome areas fixed",
            "3 confidence tiers frozen for all downstream metrics",
            "3 final readiness states frozen: Ready, Not Ready, Insufficient Data",
            "15 open validation questions formally triaged instead of left implicit",
            "5 design modules preserved and 7 execution phases remain",
        ],
        "footer": "Progress summary | Phase 0 metrics",
    },
    {
        "title": "What The MVP Contract Is Now",
        "subtitle": "This project is no longer a vague dashboard request",
        "body": [
            "Standardized intake mechanism for prospective market inputs",
            "Reproducible analytical engine tied to source fields and formula cards",
            "Three-state readiness decision with gate-level explanation",
            "Projected margin logic with explicit cost basis and exclusions",
            "Risk and mitigation output that names blocking unknowns",
            "Evidence-backed deck with plots, diagnostics, and confidence labels",
        ],
        "footer": "Locked outcome | Intake + engine + decision + deck",
    },
    {
        "title": "Authority And Confidence Framework",
        "subtitle": "Every future disagreement is now forced through one precedence and one confidence policy",
        "body": [
            "Priority 1: charter and direct Ride YourWay rules or clarifications",
            "Priority 2: observed workbook fields and workbook-derived aggregates",
            "Priority 3: PJTL assumptions, inferred logic, and design proposals",
            "Tier 1 Audited: historically reconciled and safe for headline claims",
            "Tier 2 Assumption-Backed: allowed only with ranges or caveats",
            "Tier 3 Manual Override: exposed explicitly and barred from false certainty",
        ],
        "footer": "Governance freeze | Source precedence and confidence handling",
    },
    {
        "title": "Scope Trim And Exit Strategy",
        "subtitle": "If certainty or time breaks later, the MVP still has to survive honestly",
        "body": [
            "Cut order is fixed: UI polish first, advanced scenarios second, non-core visuals third",
            "Never cut auditability, five-module logic, confidence labels, or the three-state output contract",
            "If a formula conflict cannot be resolved, branch it rather than normalizing it away",
            "If a metric cannot be defended, downgrade it to Tier 2 or Tier 3 instead of hiding the weakness",
            "If too many gate-critical metrics stay unresolved, output Insufficient Data rather than a fake go/no-go",
        ],
        "footer": "Exit strategy | Honest degradation path to MVP",
    },
    {
        "title": "Critical Blockers Carried Into Phase 1",
        "subtitle": "These were not solved in Phase 0; they were triaged and attached to explicit fallback logic",
        "body": [
            "Official Kent-Leg formula and constants",
            "Canonical billed-utilization formula",
            "Non-billable no-show denominator",
            "Pool and schedule-efficiency definitions",
            "Quarter-label ambiguity in the Q1 workbook",
            "Region-level cost detail and edge-case billing treatment",
        ],
        "footer": "Open P0 and P1 blockers | Controlled, not ignored",
    },
    {
        "title": "Immediate Next Step: Phase 1",
        "subtitle": "The build can now move into the canonical analytical base without waiting for more meetings",
        "body": [
            "Build contract-volume, vehicle-day, weekly-margin, payer, mode, SecureCare, and intake base tables",
            "Create field lineage, join-key mapping, and a missingness / ambiguity audit",
            "Quarantine unstable fields instead of forcing bad joins",
            "Freeze the minimum viable analytical subset if full integration is brittle",
            "Use Phase 0 rules to keep every future metric tied to a confidence label",
        ],
        "footer": "Phase 1 entry | Canonical analytical base",
    },
]


def xml_text(value: str) -> str:
    return escape(value, {"'": "&apos;", '"': "&quot;"})


def p_pr(bullet: bool, level: int = 0, align: str = "l") -> str:
    if bullet:
        mar_l = 342900 + (level * 228600)
        indent = -171450
        return (
            f'<a:pPr lvl="{level}" marL="{mar_l}" indent="{indent}" algn="{align}">'
            '<a:spcBef><a:spcPts val="0"/></a:spcBef>'
            '<a:spcAft><a:spcPts val="0"/></a:spcAft>'
            '<a:buChar char="•"/>'
            "</a:pPr>"
        )
    return (
        f'<a:pPr algn="{align}">'
        '<a:spcBef><a:spcPts val="0"/></a:spcBef>'
        '<a:spcAft><a:spcPts val="0"/></a:spcAft>'
        "<a:buNone/>"
        "</a:pPr>"
    )


def paragraph(
    text: str,
    *,
    size: int,
    color: str,
    bold: bool = False,
    bullet: bool = False,
    level: int = 0,
    align: str = "l",
) -> str:
    bold_attr = ' b="1"' if bold else ""
    escaped = xml_text(text)
    return (
        "<a:p>"
        f"{p_pr(bullet, level=level, align=align)}"
        f'<a:r><a:rPr lang="en-US" sz="{size}"{bold_attr}>'
        f"<a:solidFill><a:srgbClr val=\"{color}\"/></a:solidFill>"
        '<a:latin typeface="Arial"/><a:ea typeface="Arial"/><a:cs typeface="Arial"/>'
        f"</a:rPr><a:t>{escaped}</a:t></a:r>"
        f'<a:endParaRPr lang="en-US" sz="{size}">'
        f"<a:solidFill><a:srgbClr val=\"{color}\"/></a:solidFill>"
        '<a:latin typeface="Arial"/><a:ea typeface="Arial"/><a:cs typeface="Arial"/>'
        "</a:endParaRPr>"
        "</a:p>"
    )


def textbox(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    paragraphs: list[str],
    *,
    fill: str | None = None,
    line: str | None = None,
    anchor: str = "t",
) -> str:
    if fill is None:
        fill_xml = "<a:noFill/>"
    else:
        fill_xml = f"<a:solidFill><a:srgbClr val=\"{fill}\"/></a:solidFill>"

    if line is None:
        line_xml = "<a:ln><a:noFill/></a:ln>"
    else:
        line_xml = f"<a:ln w=\"9525\"><a:solidFill><a:srgbClr val=\"{line}\"/></a:solidFill></a:ln>"

    body = "".join(paragraphs) if paragraphs else "<a:p/>"

    return (
        "<p:sp>"
        "<p:nvSpPr>"
        f'<p:cNvPr id="{shape_id}" name="{xml_text(name)}"/>'
        '<p:cNvSpPr txBox="1"/>'
        "<p:nvPr/>"
        "</p:nvSpPr>"
        "<p:spPr>"
        f"<a:xfrm><a:off x=\"{x}\" y=\"{y}\"/><a:ext cx=\"{cx}\" cy=\"{cy}\"/></a:xfrm>"
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f"{fill_xml}{line_xml}"
        "</p:spPr>"
        f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}" lIns="91440" rIns="91440" tIns="45720" bIns="45720"><a:normAutofit/></a:bodyPr><a:lstStyle/>{body}</p:txBody>'
        "</p:sp>"
    )


def slide_xml(index: int, slide: dict[str, object]) -> str:
    title = str(slide["title"])
    subtitle = str(slide["subtitle"])
    body_lines = [str(item) for item in slide["body"]]
    footer = str(slide["footer"])
    pill = slide.get("pill")

    shapes = [
        textbox(2, "Top Bar", 0, 0, SLIDE_WIDTH, 320000, [], fill=ACCENT, anchor="ctr"),
        textbox(
            3,
            "Title",
            420000,
            420000,
            8_100_000,
            420000,
            [paragraph(title, size=2600, color=TEXT, bold=True)],
            anchor="ctr",
        ),
        textbox(
            4,
            "Subtitle",
            420000,
            860000,
            8_100_000,
            280000,
            [paragraph(subtitle, size=1500, color=SUBTEXT)],
        ),
        textbox(
            5,
            "Body",
            420000,
            1_280_000,
            8_000_000,
            2_950_000,
            [paragraph(line, size=1800, color=TEXT, bullet=True) for line in body_lines],
        ),
        textbox(
            6,
            "Footer",
            420000,
            4_760_000,
            8_000_000,
            180000,
            [paragraph(footer, size=1100, color=MUTED)],
            anchor="ctr",
        ),
    ]

    if pill:
        shapes.append(
            textbox(
                7,
                "Status Pill",
                7_110_000,
                380000,
                1_550_000,
                260000,
                [paragraph(str(pill), size=1200, color=PILL_TEXT, bold=True, align="ctr")],
                fill=PILL_FILL,
                anchor="ctr",
            )
        )

    shape_tree = "".join(shapes)

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f'<p:cSld name="Phase0Slide{index}"><p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
        '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        f"{shape_tree}"
        "</p:spTree></p:cSld>"
        "<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"
        "</p:sld>"
    )


def slide_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
        'Target="../slideLayouts/slideLayout11.xml"/>'
        "</Relationships>"
    )


def presentation_xml(slide_count: int) -> str:
    slide_ids = "".join(
        f'<p:sldId id="{256 + idx}" r:id="rId{5 + idx}"/>'
        for idx in range(slide_count)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        '<p:sldMasterIdLst>'
        '<p:sldMasterId id="2147483739" r:id="rId3"/>'
        '<p:sldMasterId id="2147483740" r:id="rId4"/>'
        "</p:sldMasterIdLst>"
        f"<p:sldIdLst>{slide_ids}</p:sldIdLst>"
        f'<p:sldSz cx="{SLIDE_WIDTH}" cy="{SLIDE_HEIGHT}"/>'
        '<p:notesSz cx="6858000" cy="9144000"/>'
        "</p:presentation>"
    )


def presentation_rels_xml(slide_count: int) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>',
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>',
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster2.xml"/>',
    ]
    for idx in range(slide_count):
        rid = 5 + idx
        slide_no = idx + 1
        parts.append(
            f'<Relationship Id="rId{rid}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
            f'Target="slides/slide{slide_no}.xml"/>'
        )
    parts.append("</Relationships>")
    return "".join(parts)


def root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
        "</Relationships>"
    )


def app_xml(slide_count: int) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Microsoft Macintosh PowerPoint</Application>"
        "<PresentationFormat>Widescreen</PresentationFormat>"
        f"<Slides>{slide_count}</Slides>"
        "<Notes>0</Notes><HiddenSlides>0</HiddenSlides><MMClips>0</MMClips>"
        "<ScaleCrop>false</ScaleCrop>"
        '<HeadingPairs><vt:vector size="2" baseType="variant">'
        "<vt:variant><vt:lpstr>Theme</vt:lpstr></vt:variant>"
        "<vt:variant><vt:i4>1</vt:i4></vt:variant>"
        "</vt:vector></HeadingPairs>"
        '<TitlesOfParts><vt:vector size="1" baseType="lpstr"><vt:lpstr>Office Theme</vt:lpstr></vt:vector></TitlesOfParts>'
        "<Company></Company><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>"
        "<HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion>"
        "</Properties>"
    )


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:title>Ride YourWay Phase 0 Progress</dc:title>"
        "<dc:subject>Phase 0 progress deck</dc:subject>"
        "<dc:creator>OpenAI Codex</dc:creator>"
        "<cp:lastModifiedBy>OpenAI Codex</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "<cp:revision>1</cp:revision>"
        "</cp:coreProperties>"
    )


def content_types_xml(copied_parts: list[str], slide_count: int) -> str:
    overrides = {
        "/docProps/app.xml": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        "/docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "/ppt/presentation.xml": "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
        "/ppt/presProps.xml": "application/vnd.openxmlformats-officedocument.presentationml.presProps+xml",
        "/ppt/viewProps.xml": "application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml",
    }

    for part in copied_parts:
        normalized = f"/{part}"
        if part.startswith("ppt/slideMasters/") and part.endswith(".xml"):
            overrides[normalized] = "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"
        elif part.startswith("ppt/slideLayouts/") and part.endswith(".xml"):
            overrides[normalized] = "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"
        elif part.startswith("ppt/theme/") and part.endswith(".xml"):
            overrides[normalized] = "application/vnd.openxmlformats-officedocument.theme+xml"

    for idx in range(1, slide_count + 1):
        overrides[f"/ppt/slides/slide{idx}.xml"] = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"

    override_xml = "".join(
        f'<Override PartName="{xml_text(name)}" ContentType="{xml_text(content_type)}"/>'
        for name, content_type in sorted(overrides.items())
    )

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{override_xml}"
        "</Types>"
    )


def build_deck() -> Path:
    if not TEMPLATE_PPTX.exists():
        raise FileNotFoundError(f"Template deck not found: {TEMPLATE_PPTX}")

    OUTPUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

    copied_parts: list[str] = []
    with zipfile.ZipFile(TEMPLATE_PPTX) as src, zipfile.ZipFile(OUTPUT_PPTX, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for name in src.namelist():
            if (
                name.startswith("ppt/slideMasters/")
                or name.startswith("ppt/slideLayouts/")
                or name.startswith("ppt/theme/")
                or name in {"ppt/presProps.xml", "ppt/viewProps.xml"}
            ):
                dst.writestr(name, src.read(name))
                copied_parts.append(name)

        dst.writestr("[Content_Types].xml", content_types_xml(copied_parts, len(SLIDES)))
        dst.writestr("_rels/.rels", root_rels_xml())
        dst.writestr("docProps/app.xml", app_xml(len(SLIDES)))
        dst.writestr("docProps/core.xml", core_xml())
        dst.writestr("ppt/presentation.xml", presentation_xml(len(SLIDES)))
        dst.writestr("ppt/_rels/presentation.xml.rels", presentation_rels_xml(len(SLIDES)))

        for idx, slide in enumerate(SLIDES, start=1):
            dst.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(idx, slide))
            dst.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels_xml())

    return OUTPUT_PPTX


if __name__ == "__main__":
    output = build_deck()
    print(output)
