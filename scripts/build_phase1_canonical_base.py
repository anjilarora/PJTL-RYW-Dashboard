from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
import csv
import json
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

_CODE = Path(__file__).resolve().parents[1]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
from lib.repo_paths import code_root_from_anchor, repo_root_from_anchor

ROOT = repo_root_from_anchor(Path(__file__).parent)
CODE_ROOT = code_root_from_anchor(Path(__file__).parent)
OUT_DIR = CODE_ROOT / "intermediates" / "phase1"
PJTL_RAW = CODE_ROOT / "inputs"

Q1_PATH = PJTL_RAW / "Q1 Daily Metrics 2026.xlsx"
TEMPLATE_PATH = PJTL_RAW / "RideYourWay_Prospective_Market_Intake_Template.xlsx"
EXAMPLE_PATH = PJTL_RAW / "RideYourWay_Prospective_Market_Intake_Example.xlsx"

# Repo-relative strings for lineage metadata (field_dictionary / sheet_lineage_map)
WB_Q1 = "code/inputs/Q1 Daily Metrics 2026.xlsx"
WB_TEMPLATE = "code/inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx"
WB_EXAMPLE = "code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx"

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
CELL_REF_RE = re.compile(r"([A-Z]+)([0-9]+)")
EXCEL_EPOCH = datetime(1899, 12, 30)


@dataclass
class TableSpec:
    sheet_name: str
    display_name: str
    output_name: str
    grain: str
    source_reference: str
    disposition: str
    notes: str


# Sheets that must exist for Phase-1 extraction (Q1 daily metrics workbook).
PHASE1_Q1_REQUIRED_SHEETS = frozenset(
    {
        "Contract Volume",
        "Mode Breakdown",
        "Vehicle Breakdown",
        "Weekly Margin",
        "SecureCare Profit",
    }
)
# Prospective intake workbooks (template + example) used alongside Q1.
PHASE1_INTAKE_REQUIRED_SHEETS = frozenset({"Organization Intake", "Trip Demand Input"})

TABLE_SPECS = [
    TableSpec(
        sheet_name="Contract Volume",
        display_name="Table25",
        output_name="contract_volume_base",
        grain="order_row",
        source_reference="Contract Volume!B2:R17929",
        disposition="canonical",
        notes="Primary historical ride or order fact table.",
    ),
    TableSpec(
        sheet_name="Mode Breakdown",
        display_name="Table252",
        output_name="mode_breakdown_base",
        grain="order_row",
        source_reference="Mode Breakdown!B34:S17961",
        disposition="diagnostic",
        notes="Mode-focused duplicate raw table with Trip Count; kept for reconciliation, not as the primary fact table.",
    ),
    TableSpec(
        sheet_name="Vehicle Breakdown",
        display_name="Table12",
        output_name="vehicle_day_base",
        grain="vehicle_day",
        source_reference="Vehicle Breakdown!C38:K2526",
        disposition="canonical",
        notes="Primary vehicle-day operational table.",
    ),
    TableSpec(
        sheet_name="Vehicle Breakdown",
        display_name="Table13",
        output_name="driver_active_time_base",
        grain="driver_day",
        source_reference="Vehicle Breakdown!AG37:AL2615",
        disposition="diagnostic",
        notes="Driver active-time table; row grain does not match vehicle-day grain directly.",
    ),
]

ORG_FIELD_MAP = {
    "Submission ID": "submission_id",
    "Organization name": "organization_name",
    "Organization type": "organization_type",
    "Organization Type": "organization_type",
    "Facility / program name": "facility_or_program_name",
    "Primary service area / market": "primary_service_area_market",
    "Primary city, state": "primary_city_state",
    "Primary contact name": "primary_contact_name",
    "Title": "contact_title",
    "Email": "contact_email",
    "Phone": "contact_phone",
    "Data period start": "data_period_start",
    "Data period end": "data_period_end",
    "Contract / payer name": "contract_payer_name",
    "Payer type": "payer_type",
    "Expected go-live timing": "expected_go_live_timing",
    "Primary source of trips": "primary_source_of_trips",
    "Default billing basis": "default_billing_basis",
    "Average payment term (days)": "average_payment_term",
    "Trip scheduling lead time": "trip_scheduling_lead_time",
    "Billable no-show allowed?": "billable_no_show_allowed",
    "Billable late cancel?": "billable_late_cancel",
    "Ambulatory avg price / trip": "ambulatory_avg_price_per_trip",
    "Wheelchair avg price / trip": "wheelchair_avg_price_per_trip",
    "Stretcher Alt. avg price / trip": "stretcher_alt_avg_price_per_trip",
    "SecureCare avg price / trip": "securecare_avg_price_per_trip",
    "Other mode avg price / trip": "other_mode_avg_price_per_trip",
    "Other mode description": "other_mode_description",
    "Known constraints / notes": "known_constraints_notes",
    "Typical destinations / facilities served": "typical_destinations_facilities_served",
    "Known access, hours, or handoff constraints": "known_access_hours_handoff_constraints",
    "Additional comments": "additional_comments",
    "Intake completion status": "intake_completion_status",
    "Billable protection present?": "billable_protection_present",
    "Higher-acuity pricing entered?": "higher_acuity_pricing_entered",
}


def snake_case(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def col_to_num(col: str) -> int:
    total = 0
    for char in col:
        total = total * 26 + ord(char) - 64
    return total


def num_to_col(num: int) -> str:
    letters = []
    while num:
        num, remainder = divmod(num - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def parse_ref(ref: str) -> tuple[int, int, int, int]:
    start, end = ref.split(":")
    m1 = CELL_REF_RE.fullmatch(start)
    m2 = CELL_REF_RE.fullmatch(end)
    if not m1 or not m2:
        raise ValueError(f"Unsupported ref: {ref}")
    return col_to_num(m1.group(1)), int(m1.group(2)), col_to_num(m2.group(1)), int(m2.group(2))


def excel_datetime(value: str) -> str:
    if value == "":
        return ""
    try:
        serial = float(value)
    except ValueError:
        return value
    dt = EXCEL_EPOCH + timedelta(days=serial)
    if abs(serial - int(serial)) < 1e-9:
        return dt.date().isoformat()
    return dt.isoformat(sep=" ", timespec="minutes")


def normalize_week(value: str) -> str:
    if value == "":
        return ""
    match = re.fullmatch(r"Week\s*([0-9]+)", value.strip())
    if not match:
        return value.strip()
    return f"Week {int(match.group(1))}"


def to_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


class WorkbookReader:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.zip_file = zipfile.ZipFile(path)
        self.shared_strings = self._load_shared_strings()
        self.sheet_targets = self._load_sheet_targets()
        self._sheet_rows_cache: dict[str, dict[int, dict[int, str]]] = {}
        self._sheet_tables_cache: dict[str, list[dict[str, object]]] = {}

    def close(self) -> None:
        self.zip_file.close()

    def _load_shared_strings(self) -> list[str]:
        if "xl/sharedStrings.xml" not in self.zip_file.namelist():
            return []
        root = ET.fromstring(self.zip_file.read("xl/sharedStrings.xml"))
        values: list[str] = []
        for item in root.findall("a:si", NS):
            values.append("".join(node.text or "" for node in item.iterfind(".//a:t", NS)))
        return values

    def _load_sheet_targets(self) -> dict[str, str]:
        workbook = ET.fromstring(self.zip_file.read("xl/workbook.xml"))
        rels = ET.fromstring(self.zip_file.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        targets: dict[str, str] = {}
        for sheet in workbook.find("a:sheets", NS):
            name = sheet.attrib["name"]
            target = "xl/" + rel_map[sheet.attrib[RID]]
            targets[name] = target
        return targets

    def sheet_rows(self, sheet_name: str) -> dict[int, dict[int, str]]:
        if sheet_name in self._sheet_rows_cache:
            return self._sheet_rows_cache[sheet_name]
        target = self.sheet_targets[sheet_name]
        root = ET.fromstring(self.zip_file.read(target))
        rows: dict[int, dict[int, str]] = {}
        for row in root.findall(".//a:sheetData/a:row", NS):
            row_number = int(row.attrib["r"])
            values: dict[int, str] = {}
            for cell in row.findall("a:c", NS):
                match = CELL_REF_RE.fullmatch(cell.attrib.get("r", ""))
                if not match:
                    continue
                col_num = col_to_num(match.group(1))
                values[col_num] = self._cell_value(cell)
            rows[row_number] = values
        self._sheet_rows_cache[sheet_name] = rows
        return rows

    def _cell_value(self, cell: ET.Element) -> str:
        inline = cell.find("a:is", NS)
        if inline is not None:
            return "".join(node.text or "" for node in inline.iterfind(".//a:t", NS))
        raw = cell.find("a:v", NS)
        if raw is None or raw.text is None:
            return ""
        value = raw.text
        if cell.attrib.get("t") == "s" and value.isdigit():
            index = int(value)
            if index < len(self.shared_strings):
                return self.shared_strings[index]
        return value

    def sheet_tables(self, sheet_name: str) -> list[dict[str, object]]:
        if sheet_name in self._sheet_tables_cache:
            return self._sheet_tables_cache[sheet_name]

        target = self.sheet_targets[sheet_name]
        root = ET.fromstring(self.zip_file.read(target))
        table_parts = root.find("a:tableParts", NS)
        if table_parts is None:
            self._sheet_tables_cache[sheet_name] = []
            return []

        sheet_path = PurePosixPath(target)
        rels_path = str(sheet_path.parent / "_rels" / f"{sheet_path.name}.rels")
        rel_map: dict[str, str] = {}
        if rels_path in self.zip_file.namelist():
            rels = ET.fromstring(self.zip_file.read(rels_path))
            for rel in rels:
                rel_target = rel.attrib["Target"]
                resolved = posixpath.normpath(str(sheet_path.parent / rel_target))
                rel_map[rel.attrib["Id"]] = resolved

        tables: list[dict[str, object]] = []
        for part in table_parts.findall("a:tablePart", NS):
            target_path = rel_map.get(part.attrib[RID])
            if not target_path:
                continue
            table_root = ET.fromstring(self.zip_file.read(target_path))
            columns = [
                column.attrib.get("name", "")
                for column in table_root.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}tableColumns")
            ]
            tables.append(
                {
                    "path": target_path,
                    "name": table_root.attrib.get("name"),
                    "display_name": table_root.attrib.get("displayName"),
                    "ref": table_root.attrib.get("ref"),
                    "columns": columns,
                }
            )
        self._sheet_tables_cache[sheet_name] = tables
        return tables

    def extract_table(self, sheet_name: str, display_name: str) -> list[dict[str, str]]:
        table = None
        for candidate in self.sheet_tables(sheet_name):
            if candidate["display_name"] == display_name or candidate["name"] == display_name:
                table = candidate
                break
        if table is None:
            raise KeyError(f"Table {display_name} not found in {sheet_name}")

        start_col, start_row, end_col, end_row = parse_ref(str(table["ref"]))
        columns = list(table["columns"])
        rows = self.sheet_rows(sheet_name)
        records: list[dict[str, str]] = []

        for row_number in range(start_row + 1, end_row + 1):
            row_values = rows.get(row_number, {})
            record: dict[str, str] = {}
            nonempty = 0
            for offset, column_name in enumerate(columns):
                col_num = start_col + offset
                value = row_values.get(col_num, "")
                record[snake_case(column_name)] = value
                if value != "":
                    nonempty += 1
            if nonempty == 0:
                continue
            records.append(record)
        return records


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def extract_trip_demand(reader: WorkbookReader, sheet_name: str, workbook_variant: str) -> list[dict[str, str]]:
    rows = reader.sheet_rows(sheet_name)
    header_row = None
    for row_number in sorted(rows):
        values = list(rows[row_number].values())
        if "Row ID" in values and "Trip Mode" in values:
            header_row = row_number
            break
    if header_row is None:
        raise ValueError(f"Could not find trip demand header row in {sheet_name}")

    header_values = rows[header_row]
    max_col = max(header_values)
    headers = [header_values.get(col, "") for col in range(1, max_col + 1)]
    records: list[dict[str, str]] = []
    blank_streak = 0

    for row_number in range(header_row + 1, max(rows) + 1):
        row = rows.get(row_number, {})
        values = [row.get(col, "") for col in range(1, max_col + 1)]
        if all(value == "" for value in values):
            if records:
                blank_streak += 1
                if blank_streak >= 1:
                    break
            continue
        blank_streak = 0
        record = {"workbook_variant": workbook_variant, "source_sheet": sheet_name, "source_row": row_number}
        nonempty = 0
        for index, header in enumerate(headers, start=1):
            if header == "":
                continue
            record[snake_case(header)] = values[index - 1]
            if values[index - 1] != "":
                nonempty += 1
        if nonempty == 0:
            continue
        records.append(record)
    return records


def extract_org_intake(reader: WorkbookReader, sheet_name: str, workbook_variant: str) -> list[dict[str, str]]:
    rows = reader.sheet_rows(sheet_name)
    results: list[dict[str, str]] = []
    current_section = "unassigned"
    for row_number in sorted(rows):
        row = rows[row_number]
        values = [row.get(col, "") for col in range(1, 7)]
        nonempty = [value for value in values if value != ""]
        if len(nonempty) == 1 and values[0] != "":
            current_section = values[0]
            continue
        for label_col, value_col in ((1, 2), (3, 4), (5, 6)):
            label = row.get(label_col, "").strip()
            value = row.get(value_col, "").strip()
            if label == "":
                continue
            results.append(
                {
                    "workbook_variant": workbook_variant,
                    "source_sheet": sheet_name,
                    "source_row": row_number,
                    "section": current_section,
                    "field_label": label,
                    "field_name": snake_case(label),
                    "field_value": value,
                }
            )
    return results


def org_metadata_map(org_rows: list[dict[str, str]]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for row in org_rows:
        label = row["field_label"]
        mapped = ORG_FIELD_MAP.get(label)
        if mapped:
            metadata[mapped] = row["field_value"]
    return metadata


def augment_date_fields(records: list[dict[str, str]], date_fields: list[str], datetime_fields: list[str]) -> list[dict[str, str]]:
    augmented: list[dict[str, str]] = []
    for record in records:
        updated = dict(record)
        for field in date_fields:
            raw = updated.get(field, "")
            updated[f"{field}_iso"] = excel_datetime(raw)
        for field in datetime_fields:
            raw = updated.get(field, "")
            updated[f"{field}_iso"] = excel_datetime(raw)
        if "week" in updated:
            updated["week_normalized"] = normalize_week(updated.get("week", ""))
        augmented.append(updated)
    return augmented


def parse_weekly_margin_blocks(reader: WorkbookReader, sheet_name: str) -> list[dict[str, str]]:
    rows = reader.sheet_rows(sheet_name)
    records: list[dict[str, str]] = []

    def build_record(scope_level: str, scope_label: str, row_number: int) -> dict[str, str]:
        row = rows.get(row_number, {})
        return {
            "scope_level": scope_level,
            "scope_label": scope_label,
            "week_normalized": normalize_week(scope_label) if scope_level == "week" else "",
            "day": row.get(2, ""),
            "total_revenue": row.get(4, ""),
            "total_cost": row.get(6, ""),
            "profit_margin": row.get(8, ""),
            "dollar_profit": row.get(10, ""),
            "fixed_overhead_cost": row.get(13, ""),
            "fixed_operating_cost": row.get(15, ""),
            "gas": row.get(17, ""),
            "driver_wage": row.get(19, ""),
            "total_cost_check": row.get(21, ""),
            "capx": row.get(23, ""),
            "post_capx_margin": row.get(24, ""),
            "overhead_balance_total_revenue": row.get(26, ""),
            "overhead_balance_total_cost": row.get(27, ""),
            "overhead_balance_profit_margin": row.get(28, ""),
            "office_wage_overhead": row.get(29, ""),
            "max_allowance": row.get(30, ""),
            "percent_revenue": row.get(31, ""),
            "percent_cost": row.get(32, ""),
            "source_sheet": sheet_name,
            "source_row": row_number,
        }

    quarter_label = rows.get(3, {}).get(2, "Quarter Summary")
    for row_number in range(6, 13):
        record = build_record("quarter_total", quarter_label, row_number)
        if record["day"] != "":
            records.append(record)

    for row_number in sorted(rows):
        label = rows[row_number].get(2, "")
        if re.fullmatch(r"Week \d+", label):
            scope_label = label
            data_row = row_number + 3
            block_records: list[dict[str, str]] = []
            while True:
                record = build_record("week", scope_label, data_row)
                if record["day"] == "":
                    break
                block_records.append(record)
                if record["day"] == "Total":
                    break
                data_row += 1
            if block_has_signal(block_records):
                records.extend(block_records)
    return records


def parse_securecare_blocks(reader: WorkbookReader, sheet_name: str) -> list[dict[str, str]]:
    rows = reader.sheet_rows(sheet_name)
    records: list[dict[str, str]] = []

    def build_record(scope_level: str, scope_label: str, row_number: int) -> dict[str, str]:
        row = rows.get(row_number, {})
        return {
            "scope_level": scope_level,
            "scope_label": scope_label,
            "week_normalized": normalize_week(scope_label) if scope_level == "week" else "",
            "day": row.get(2, ""),
            "total_revenue": row.get(4, ""),
            "total_cost": row.get(6, ""),
            "profit_margin": row.get(8, ""),
            "dollar_profit": row.get(10, ""),
            "fixed_overhead_cost": row.get(13, ""),
            "fixed_operating_cost": row.get(15, ""),
            "gas": row.get(17, ""),
            "driver_wage": row.get(19, ""),
            "total_cost_check": row.get(21, ""),
            "source_sheet": sheet_name,
            "source_row": row_number,
        }

    quarter_label = rows.get(3, {}).get(2, "Quarter Summary")
    for row_number in range(6, 13):
        record = build_record("quarter_total", quarter_label, row_number)
        if record["day"] != "":
            records.append(record)

    for row_number in sorted(rows):
        label = rows[row_number].get(2, "")
        if re.fullmatch(r"Week \d+", label):
            scope_label = label
            data_row = row_number + 3
            block_records: list[dict[str, str]] = []
            while True:
                record = build_record("week", scope_label, data_row)
                if record["day"] == "":
                    break
                block_records.append(record)
                if record["day"] == "Total":
                    break
                data_row += 1
            if block_has_signal(block_records):
                records.extend(block_records)
    return records


def block_has_signal(records: list[dict[str, str]]) -> bool:
    for record in records:
        for field in ("total_revenue", "total_cost", "dollar_profit", "fixed_overhead_cost"):
            value = to_float(record.get(field, ""))
            if value is not None and abs(value) > 0:
                return True
    return False


def group_records(rows: list[dict[str, str]], keys: list[str], output_name: str) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], dict[str, object]] = {}
    for row in rows:
        if row.get("payer_id", "") == "" and row.get("order_mode", "") == "" and output_name != "prospective":
            continue
        key = tuple(row.get(key, "") for key in keys)
        entry = grouped.setdefault(
            key,
            {key_name: key[index] for index, key_name in enumerate(keys)}
            | {
                "order_count": 0,
                "sum_order_price": 0.0,
                "sum_order_mileage": 0.0,
                "sum_kent_legs": 0.0,
                "completed_count": 0,
                "billed_no_show_count": 0,
                "non_billable_no_show_count": 0,
            },
        )
        entry["order_count"] += 1
        entry["sum_order_price"] += to_float(row.get("order_price", "")) or 0.0
        entry["sum_order_mileage"] += to_float(row.get("order_mileage", "")) or 0.0
        entry["sum_kent_legs"] += to_float(row.get("kent_legs", "")) or 0.0
        if row.get("order_status", "") == "Completed":
            entry["completed_count"] += 1
        reason = row.get("reason", "")
        if reason == "Billed no show":
            entry["billed_no_show_count"] += 1
        if row.get("order_status", "") == "No show" and reason != "Billed no show":
            entry["non_billable_no_show_count"] += 1
    results = list(grouped.values())
    results.sort(key=lambda item: tuple(str(item.get(key, "")) for key in keys))
    return results


def infer_unit(field_name: str) -> str:
    if field_name.endswith("_iso"):
        return "iso_date_or_datetime"
    if any(token in field_name for token in ["price", "revenue", "cost", "profit", "overhead", "allowance"]):
        return "usd"
    if any(token in field_name for token in ["margin", "rate", "share", "percent", "utilization", "ratio"]):
        return "ratio_0_1"
    if any(token in field_name for token in ["mileage", "miles"]):
        return "miles"
    if any(token in field_name for token in ["road_time", "active_time", "hour"]):
        return "hours"
    if "date" in field_name:
        return "excel_serial_date"
    if "time" in field_name:
        return "excel_serial_datetime"
    if any(token in field_name for token in ["kent_legs", "trip", "count"]):
        return "count"
    if field_name in {"vehicle", "name", "payer_id", "order_mode", "order_status", "reason", "day", "week", "pu_zone", "do_zone"}:
        return "categorical"
    return "text_or_categorical"


def infer_module(table_name: str, field_name: str) -> str:
    if table_name in {"vehicle_day_base", "driver_active_time_base"}:
        return "module_3_capacity_and_scheduling"
    if table_name in {"weekly_margin_base", "securecare_profit_base"}:
        if any(token in field_name for token in ["revenue", "margin", "profit"]):
            return "module_5_revenue_and_margin"
        if any(token in field_name for token in ["cost", "gas", "wage", "overhead", "capx"]):
            return "module_4_cost"
        return "cross_cutting"
    if table_name == "prospective_intake_base":
        if any(token in field_name for token in ["price", "billing", "payer", "billable", "contract"]):
            return "module_2_contract_business_model"
        return "module_1_demand"
    if table_name in {"payer_summary_base"}:
        return "module_2_contract_business_model"
    if table_name in {"mode_summary_base"}:
        return "module_5_revenue_and_margin"
    if table_name in {"contract_volume_base", "mode_breakdown_base"}:
        if any(token in field_name for token in ["price", "kent_legs"]):
            return "cross_cutting"
        if field_name in {"payer_id", "order_status", "reason"}:
            return "module_2_contract_business_model"
        if field_name in {"date_of_service", "date_of_service_iso", "pick_up_time", "pick_up_time_iso", "day", "week"}:
            return "module_3_capacity_and_scheduling"
        return "cross_cutting"
    return "cross_cutting"


def infer_join_strategy(table_name: str, field_name: str) -> str:
    if field_name in {"date_of_service", "date_of_service_iso", "date", "date_iso", "day", "week"}:
        return "time_aggregate"
    if field_name in {"payer_id", "payer_type", "contract_payer_name"}:
        return "payer_or_contract_aggregate"
    if field_name in {"order_mode", "order_mode2", "trip_mode", "mode"}:
        return "mode_aggregate"
    if field_name in {"vehicle", "name"}:
        return "within_table_only"
    if table_name == "prospective_intake_base":
        return "prospective_only"
    return "none"


def build_field_dictionary(table_rows: dict[str, list[dict[str, object]]]) -> list[dict[str, str]]:
    source_lookup = {
        "contract_volume_base": (WB_Q1, "Contract Volume", "Table25", "canonical"),
        "mode_breakdown_base": (WB_Q1, "Mode Breakdown", "Table252", "diagnostic"),
        "payer_summary_base": ("Derived from contract_volume_base", "Derived", "groupby(payer_id, week, day, order_status)", "canonical"),
        "mode_summary_base": ("Derived from contract_volume_base", "Derived", "groupby(order_mode, week, day, order_status)", "canonical"),
        "vehicle_day_base": (WB_Q1, "Vehicle Breakdown", "Table12", "canonical"),
        "driver_active_time_base": (WB_Q1, "Vehicle Breakdown", "Table13", "diagnostic"),
        "weekly_margin_base": (WB_Q1, "Weekly Margin", "manual report blocks", "canonical"),
        "securecare_profit_base": (WB_Q1, "SecureCare Profit", "manual report blocks", "canonical"),
        "prospective_trip_demand_template": (WB_TEMPLATE, "Trip Demand Input", "row-oriented input block", "diagnostic"),
        "prospective_trip_demand_example": (WB_EXAMPLE, "Trip Demand Input", "row-oriented input block", "canonical"),
        "prospective_org_intake_template_long": (WB_TEMPLATE, "Organization Intake", "paired form fields", "diagnostic"),
        "prospective_org_intake_example_long": (WB_EXAMPLE, "Organization Intake", "paired form fields", "canonical"),
        "prospective_intake_base": (WB_EXAMPLE, "Organization Intake + Trip Demand Input", "merged org metadata into trip demand rows", "canonical"),
    }
    dictionary_rows: list[dict[str, str]] = []
    for table_name, rows in table_rows.items():
        if not rows:
            continue
        source_workbook, source_sheet, source_reference, disposition = source_lookup[table_name]
        for field_name in rows[0].keys():
            dictionary_rows.append(
                {
                    "output_table": table_name,
                    "field_name": field_name,
                    "source_workbook": source_workbook,
                    "source_sheet": source_sheet,
                    "source_reference": source_reference,
                    "grain": table_grain(table_name),
                    "unit": infer_unit(field_name),
                    "join_strategy": infer_join_strategy(table_name, field_name),
                    "module_assignment": infer_module(table_name, field_name),
                    "disposition": disposition,
                    "notes": field_notes(table_name, field_name),
                }
            )
    return dictionary_rows


def field_notes(table_name: str, field_name: str) -> str:
    if table_name == "contract_volume_base" and field_name in {"date_of_service_iso", "pick_up_time_iso"}:
        return "Derived from Excel serial values in the source workbook."
    if table_name == "vehicle_day_base" and field_name == "mode":
        return "Vehicle-day rows carry a dominant mode label but do not expose region directly."
    if table_name == "driver_active_time_base":
        return "Driver-day table does not share a direct vehicle key with vehicle_day_base."
    if table_name == "prospective_intake_base":
        return "Built by repeating organization-level metadata onto service-line demand rows."
    if table_name in {"payer_summary_base", "mode_summary_base"}:
        return "Derived summary table created during Phase 1 to stabilize downstream joins."
    return ""


def table_grain(table_name: str) -> str:
    grain_map = {
        "contract_volume_base": "order_row",
        "mode_breakdown_base": "order_row",
        "payer_summary_base": "payer_week_day_status",
        "mode_summary_base": "mode_week_day_status",
        "vehicle_day_base": "vehicle_day",
        "driver_active_time_base": "driver_day",
        "weekly_margin_base": "scope_day",
        "securecare_profit_base": "scope_day",
        "prospective_trip_demand_template": "service_line_row",
        "prospective_trip_demand_example": "service_line_row",
        "prospective_org_intake_template_long": "field_row",
        "prospective_org_intake_example_long": "field_row",
        "prospective_intake_base": "service_line_row",
    }
    return grain_map.get(table_name, "unknown")


def build_unit_dictionary(field_dictionary: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in field_dictionary:
        rows.append(
            {
                "output_table": field["output_table"],
                "field_name": field["field_name"],
                "unit": field["unit"],
                "grain": field["grain"],
                "notes": field["notes"],
            }
        )
    return rows


def build_sheet_lineage() -> list[dict[str, str]]:
    return [
        {
            "source_workbook": WB_Q1,
            "source_sheet": "Contract Volume",
            "extraction_type": "excel_table",
            "source_reference": "Table25 / B2:R17929",
            "output_artifact": "contract_volume_base.csv",
            "grain": "order_row",
            "status": "canonical",
            "notes": "Primary historical fact table.",
        },
        {
            "source_workbook": WB_Q1,
            "source_sheet": "Mode Breakdown",
            "extraction_type": "excel_table",
            "source_reference": "Table252 / B34:S17961",
            "output_artifact": "mode_breakdown_base.csv",
            "grain": "order_row",
            "status": "diagnostic",
            "notes": "Mode-focused duplicate raw table with Trip Count.",
        },
        {
            "source_workbook": WB_Q1,
            "source_sheet": "Revenue by Payer",
            "extraction_type": "duplicate_raw_sheet",
            "source_reference": "Table2527 / B2:R17929",
            "output_artifact": "not_extracted_as_primary",
            "grain": "order_row",
            "status": "quarantined",
            "notes": "Raw duplicate of Contract Volume; better handled as a derived summary from the canonical fact table.",
        },
        {
            "source_workbook": WB_Q1,
            "source_sheet": "Vehicle Breakdown",
            "extraction_type": "excel_table",
            "source_reference": "Table12 / C38:K2526",
            "output_artifact": "vehicle_day_base.csv",
            "grain": "vehicle_day",
            "status": "canonical",
            "notes": "Primary operational vehicle table.",
        },
        {
            "source_workbook": WB_Q1,
            "source_sheet": "Vehicle Breakdown",
            "extraction_type": "excel_table",
            "source_reference": "Table13 / AG37:AL2615",
            "output_artifact": "driver_active_time_base.csv",
            "grain": "driver_day",
            "status": "diagnostic",
            "notes": "Driver active-time companion table with grain mismatch versus vehicle_day_base.",
        },
        {
            "source_workbook": WB_Q1,
            "source_sheet": "Weekly Margin",
            "extraction_type": "manual_block_extractor",
            "source_reference": "Quarter total block plus repeating week blocks",
            "output_artifact": "weekly_margin_base.csv",
            "grain": "scope_day",
            "status": "canonical",
            "notes": "Merged report layout required manual block parsing.",
        },
        {
            "source_workbook": WB_Q1,
            "source_sheet": "SecureCare Profit",
            "extraction_type": "manual_block_extractor",
            "source_reference": "Quarter total block plus repeating week blocks",
            "output_artifact": "securecare_profit_base.csv",
            "grain": "scope_day",
            "status": "canonical",
            "notes": "SecureCare-specific economic summary for higher-acuity analysis.",
        },
        {
            "source_workbook": WB_TEMPLATE,
            "source_sheet": "Organization Intake",
            "extraction_type": "paired_form_fields",
            "source_reference": "A:F key-value layout",
            "output_artifact": "prospective_org_intake_template_long.csv",
            "grain": "field_row",
            "status": "diagnostic",
            "notes": "Schema contract for external input collection.",
        },
        {
            "source_workbook": WB_EXAMPLE,
            "source_sheet": "Organization Intake",
            "extraction_type": "paired_form_fields",
            "source_reference": "A:F key-value layout",
            "output_artifact": "prospective_org_intake_example_long.csv",
            "grain": "field_row",
            "status": "canonical",
            "notes": "Filled example establishes semantics for intake fields.",
        },
        {
            "source_workbook": WB_TEMPLATE,
            "source_sheet": "Trip Demand Input",
            "extraction_type": "row_oriented_form",
            "source_reference": "Header plus service-line rows",
            "output_artifact": "prospective_trip_demand_template.csv",
            "grain": "service_line_row",
            "status": "diagnostic",
            "notes": "Input schema including derived workbook fields.",
        },
        {
            "source_workbook": WB_EXAMPLE,
            "source_sheet": "Trip Demand Input",
            "extraction_type": "row_oriented_form",
            "source_reference": "Header plus service-line rows",
            "output_artifact": "prospective_trip_demand_example.csv",
            "grain": "service_line_row",
            "status": "canonical",
            "notes": "Primary prospective service-line example for MVP demonstration.",
        },
        {
            "source_workbook": WB_EXAMPLE,
            "source_sheet": "Organization Intake + Trip Demand Input",
            "extraction_type": "phase1_merge",
            "source_reference": "Organization metadata repeated onto service-line rows",
            "output_artifact": "prospective_intake_base.csv",
            "grain": "service_line_row",
            "status": "canonical",
            "notes": "Minimum viable prospective base table for downstream scenario work.",
        },
    ]


def build_join_inventory() -> list[dict[str, str]]:
    return [
        {
            "left_table": "contract_volume_base",
            "right_table": "payer_summary_base",
            "candidate_keys": "payer_id + week_normalized + day + order_status",
            "join_level": "derived_aggregate",
            "status": "recommended",
            "notes": "payer_summary_base is derived directly from contract_volume_base and should not be treated as an independent external source.",
        },
        {
            "left_table": "contract_volume_base",
            "right_table": "mode_summary_base",
            "candidate_keys": "order_mode + week_normalized + day + order_status",
            "join_level": "derived_aggregate",
            "status": "recommended",
            "notes": "Mode summary is generated from the canonical fact table.",
        },
        {
            "left_table": "contract_volume_base",
            "right_table": "weekly_margin_base",
            "candidate_keys": "week_normalized + day",
            "join_level": "aggregate_only",
            "status": "possible_with_caution",
            "notes": "Grains differ materially; use only for time-bucket comparison, not row-level joins.",
        },
        {
            "left_table": "contract_volume_base",
            "right_table": "vehicle_day_base",
            "candidate_keys": "date_of_service_iso + week_normalized + day",
            "join_level": "aggregate_only",
            "status": "possible_with_caution",
            "notes": "No direct vehicle or route key exists in contract_volume_base.",
        },
        {
            "left_table": "vehicle_day_base",
            "right_table": "driver_active_time_base",
            "candidate_keys": "date_iso + week_normalized + day",
            "join_level": "day_level_only",
            "status": "not_recommended_at_row_grain",
            "notes": "vehicle_day_base uses vehicle IDs while driver_active_time_base uses names; row-grain joins would be fabricated.",
        },
        {
            "left_table": "prospective_intake_base",
            "right_table": "contract_volume_base",
            "candidate_keys": "none_directly; use analog dimensions such as mode, day, and service class",
            "join_level": "scenario_only",
            "status": "not_directly_joinable",
            "notes": "Prospective data is a future-state input contract, not a shared key extension of the historical fact table.",
        },
        {
            "left_table": "prospective_intake_base",
            "right_table": "weekly_margin_base",
            "candidate_keys": "none_directly; compare through scenario assumptions",
            "join_level": "scenario_only",
            "status": "not_directly_joinable",
            "notes": "Economic comparison is model-based, not key-based.",
        },
    ]


def build_quarantine_list() -> list[dict[str, str]]:
    return [
        {
            "source_sheet_or_field": "Revenue by Payer raw table",
            "status": "quarantined_from_primary_base",
            "reason": "Duplicates Contract Volume at raw grain and risks conflicting ownership of the primary fact table.",
            "fallback": "Use derived payer_summary_base from contract_volume_base.",
        },
        {
            "source_sheet_or_field": "Mode Breakdown pivot blocks outside Table252",
            "status": "diagnostic_only",
            "reason": "Sheet mixes raw rows with pivot-style summaries and grand-total side panels.",
            "fallback": "Use Table252 raw rows plus derived mode_summary_base.",
        },
        {
            "source_sheet_or_field": "Vehicle Breakdown side panels and weekly metric blocks",
            "status": "diagnostic_only",
            "reason": "Sheet contains multiple side-by-side summaries with incompatible grains.",
            "fallback": "Use Table12 and Table13 only as canonical extracted structures.",
        },
        {
            "source_sheet_or_field": "OTP sheet",
            "status": "quarantined",
            "reason": "Still unresolved in the validation backlog and not needed to pass Phase 1.",
            "fallback": "Exclude from the Phase 1 canonical base.",
        },
        {
            "source_sheet_or_field": "Heat Map sheet",
            "status": "diagnostic_only",
            "reason": "Useful for later EDA visuals but not required for the minimum viable analytical subset.",
            "fallback": "Defer to Phase 3 descriptive analysis.",
        },
        {
            "source_sheet_or_field": "Total Performance / Regional Performance / Corewell Metrics",
            "status": "diagnostic_only",
            "reason": "High-value reporting sheets, but not needed to establish a clean row-grain canonical base.",
            "fallback": "Use later for reconciliation and diagnostics, not as the primary extract source.",
        },
        {
            "source_sheet_or_field": "Quarter labels in Q1 workbook",
            "status": "ambiguity_flag",
            "reason": "Workbook contains Quarter four and Quarter one labels despite file name implying Q1 2026.",
            "fallback": "Preserve raw labels and surface the ambiguity in the Phase 1 note.",
        },
    ]


def build_minimum_viable_subset() -> list[dict[str, str]]:
    return [
        {
            "artifact": "contract_volume_base.csv",
            "status": "required",
            "why_needed": "Core historical fact table for demand, no-show, price, and Kent-Leg analysis.",
        },
        {
            "artifact": "vehicle_day_base.csv",
            "status": "required",
            "why_needed": "Canonical operational capacity table for road time, mileage, and Kent-Leg output at vehicle-day grain.",
        },
        {
            "artifact": "weekly_margin_base.csv",
            "status": "required",
            "why_needed": "Historical cost and margin reference for economic calibration.",
        },
        {
            "artifact": "securecare_profit_base.csv",
            "status": "required",
            "why_needed": "Higher-acuity and SecureCare economics are part of the charter gates and design notes.",
        },
        {
            "artifact": "prospective_intake_base.csv",
            "status": "required",
            "why_needed": "Minimum viable prospective scenario input table for MVP demonstrations.",
        },
        {
            "artifact": "payer_summary_base.csv",
            "status": "required",
            "why_needed": "Stabilizes contract concentration and payer-level reimbursement analysis without relying on the duplicate raw sheet.",
        },
        {
            "artifact": "driver_active_time_base.csv",
            "status": "supplementary",
            "why_needed": "Needed for later active-time diagnostics, but not required for the minimum viable subset if join issues remain.",
        },
        {
            "artifact": "mode_breakdown_base.csv",
            "status": "supplementary",
            "why_needed": "Helpful for mode reconciliation and trip-count validation, but not required as the primary fact source.",
        },
    ]


def build_missingness_audit(table_rows: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    audit_rows: list[dict[str, object]] = []
    for table_name, rows in table_rows.items():
        if not rows:
            continue
        row_count = len(rows)
        columns = list(rows[0].keys())
        for column in columns:
            values = [row.get(column, "") for row in rows]
            missing_count = sum(1 for value in values if value in {"", None})
            nonblank_values = [str(value) for value in values if value not in {"", None}]
            audit_rows.append(
                {
                    "table_name": table_name,
                    "field_name": column,
                    "row_count": row_count,
                    "missing_count": missing_count,
                    "missing_pct": round(missing_count / row_count, 6),
                    "nonblank_count": row_count - missing_count,
                    "unique_nonblank_count": len(set(nonblank_values)),
                }
            )
    return audit_rows


def filter_records(rows: list[dict[str, str]], required_any: list[str]) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    for row in rows:
        if any(row.get(field, "") not in {"", None} for field in required_any):
            filtered.append(row)
    return filtered


def list_xlsx_sheet_names(path: Path) -> set[str]:
    """Return workbook sheet tab names for an .xlsx file."""
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("xl/workbook.xml"))
    sheets_el = root.find("a:sheets", NS)
    if sheets_el is None:
        return set()
    return {sh.attrib["name"] for sh in sheets_el}


def validate_phase1_workbooks(q1: Path, template: Path, example: Path) -> None:
    """Fail fast with clear errors if required sheets are missing."""
    q1_names = list_xlsx_sheet_names(q1)
    missing_q1 = sorted(PHASE1_Q1_REQUIRED_SHEETS - q1_names)
    if missing_q1:
        raise ValueError(f"Q1 workbook missing sheets: {missing_q1}; found: {sorted(q1_names)}")
    for label, book in ("template", template), ("example", example):
        names = list_xlsx_sheet_names(book)
        miss = sorted(PHASE1_INTAKE_REQUIRED_SHEETS - names)
        if miss:
            raise ValueError(f"{label} workbook missing sheets: {miss}; found: {sorted(names)}")


def run_phase1_extract(
    q1_path: Path,
    out_dir: Path,
    template_path: Path,
    example_path: Path,
) -> dict[str, object]:
    """
    Extract Phase-1 canonical CSVs into ``out_dir`` (caller creates parent dirs).

    Returns the same summary dict previously printed by ``main()``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    q1 = WorkbookReader(q1_path)
    template = WorkbookReader(template_path)
    example = WorkbookReader(example_path)

    try:
        contract_volume = filter_records(
            augment_date_fields(q1.extract_table("Contract Volume", "Table25"), ["date_of_service"], ["pick_up_time"]),
            ["payer_id", "order_mode", "date_of_service", "week"],
        )
        mode_breakdown = filter_records(
            augment_date_fields(q1.extract_table("Mode Breakdown", "Table252"), ["date_of_service"], ["pick_up_time"]),
            ["payer_id", "order_mode", "date_of_service", "week", "trip_count"],
        )
        vehicle_day = filter_records(
            augment_date_fields(q1.extract_table("Vehicle Breakdown", "Table12"), ["date"], []),
            ["date", "vehicle", "week", "road_time"],
        )
        driver_active_time = filter_records(
            augment_date_fields(q1.extract_table("Vehicle Breakdown", "Table13"), ["date"], []),
            ["date", "name", "week", "road_time", "active_time"],
        )
        weekly_margin = filter_records(parse_weekly_margin_blocks(q1, "Weekly Margin"), ["scope_label", "day", "total_revenue"])
        securecare_profit = filter_records(parse_securecare_blocks(q1, "SecureCare Profit"), ["scope_label", "day", "total_revenue"])

        org_template_long = extract_org_intake(template, "Organization Intake", "template")
        org_example_long = extract_org_intake(example, "Organization Intake", "example")
        trip_template = filter_records(
            extract_trip_demand(template, "Trip Demand Input", "template"),
            ["contract_program", "trip_mode", "completed_trips_week", "avg_revenue_completed_trip"],
        )
        trip_example = filter_records(
            extract_trip_demand(example, "Trip Demand Input", "example"),
            ["contract_program", "trip_mode", "completed_trips_week", "avg_revenue_completed_trip"],
        )

        example_metadata = org_metadata_map(org_example_long)
        prospective_intake = []
        for row in trip_example:
            enriched = dict(example_metadata)
            enriched.update(row)
            prospective_intake.append(enriched)

        payer_summary = group_records(contract_volume, ["payer_id", "week_normalized", "day", "order_status"], "payer_summary")
        mode_summary = group_records(contract_volume, ["order_mode", "week_normalized", "day", "order_status"], "mode_summary")

        table_rows: dict[str, list[dict[str, object]]] = {
            "contract_volume_base": contract_volume,
            "mode_breakdown_base": mode_breakdown,
            "payer_summary_base": payer_summary,
            "mode_summary_base": mode_summary,
            "vehicle_day_base": vehicle_day,
            "driver_active_time_base": driver_active_time,
            "weekly_margin_base": weekly_margin,
            "securecare_profit_base": securecare_profit,
            "prospective_org_intake_template_long": org_template_long,
            "prospective_org_intake_example_long": org_example_long,
            "prospective_trip_demand_template": trip_template,
            "prospective_trip_demand_example": trip_example,
            "prospective_intake_base": prospective_intake,
        }

        write_csv(out_dir / "contract_volume_base.csv", contract_volume)
        write_csv(out_dir / "mode_breakdown_base.csv", mode_breakdown)
        write_csv(out_dir / "payer_summary_base.csv", payer_summary)
        write_csv(out_dir / "mode_summary_base.csv", mode_summary)
        write_csv(out_dir / "vehicle_day_base.csv", vehicle_day)
        write_csv(out_dir / "driver_active_time_base.csv", driver_active_time)
        write_csv(out_dir / "weekly_margin_base.csv", weekly_margin)
        write_csv(out_dir / "securecare_profit_base.csv", securecare_profit)
        write_csv(out_dir / "prospective_org_intake_template_long.csv", org_template_long)
        write_csv(out_dir / "prospective_org_intake_example_long.csv", org_example_long)
        write_csv(out_dir / "prospective_trip_demand_template.csv", trip_template)
        write_csv(out_dir / "prospective_trip_demand_example.csv", trip_example)
        write_csv(out_dir / "prospective_intake_base.csv", prospective_intake)

        field_dictionary = build_field_dictionary(table_rows)
        unit_dictionary = build_unit_dictionary(field_dictionary)
        sheet_lineage = build_sheet_lineage()
        join_inventory = build_join_inventory()
        quarantine_list = build_quarantine_list()
        minimum_viable_subset = build_minimum_viable_subset()
        missingness_audit = build_missingness_audit(table_rows)

        write_csv(out_dir / "field_dictionary.csv", field_dictionary)
        write_csv(out_dir / "unit_dictionary.csv", unit_dictionary)
        write_csv(out_dir / "sheet_lineage_map.csv", sheet_lineage)
        write_csv(out_dir / "join_key_inventory.csv", join_inventory)
        write_csv(out_dir / "quarantine_list.csv", quarantine_list)
        write_csv(out_dir / "minimum_viable_subset.csv", minimum_viable_subset)
        write_csv(out_dir / "missingness_audit.csv", missingness_audit)

        summary: dict[str, object] = {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "output_dir": str(out_dir.relative_to(ROOT)) if ROOT in out_dir.parents or out_dir == ROOT else str(out_dir),
            "table_row_counts": {name: len(rows) for name, rows in table_rows.items()},
            "quarantine_count": len(quarantine_list),
            "join_inventory_count": len(join_inventory),
            "minimum_viable_subset_count": len(minimum_viable_subset),
        }
        (out_dir / "phase1_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary
    finally:
        q1.close()
        template.close()
        example.close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build Phase-1 canonical base CSVs from Q1 + intake workbooks.")
    parser.add_argument("--q1", type=Path, default=Q1_PATH, help="Path to Q1 Daily Metrics .xlsx")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="Output directory for CSVs")
    parser.add_argument("--template", type=Path, default=TEMPLATE_PATH, help="Prospective market intake template .xlsx")
    parser.add_argument("--example", type=Path, default=EXAMPLE_PATH, help="Prospective market intake example .xlsx")
    parser.add_argument("--skip-validate", action="store_true", help="Skip sheet presence checks (not recommended)")
    args = parser.parse_args()

    if not args.skip_validate:
        validate_phase1_workbooks(args.q1, args.template, args.example)
    summary = run_phase1_extract(args.q1, args.out_dir, args.template, args.example)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
