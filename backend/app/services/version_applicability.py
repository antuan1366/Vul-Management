import re
from dataclasses import dataclass


@dataclass
class ApplicabilityResult:
    status: str
    confidence: float
    reason: str


def _cpe_unescape(value: str) -> str:
    return value.replace("\\:", ":").replace("\\!", "!").replace("\\?", "?")


def cpe_version(cpe: str) -> str | None:
    parts = cpe.split(":")
    if len(parts) >= 6 and parts[0] == "cpe" and parts[1] == "2.3":
        return _cpe_unescape(parts[5])
    if cpe.startswith("cpe:/"):
        legacy = cpe[5:].split(":")
        return _cpe_unescape(legacy[2]) if len(legacy) >= 3 else None
    return None


def _tokenize(version: str) -> list[tuple[int, object]]:
    values: list[tuple[int, object]] = []
    for token in re.split(r"[._+\-~]", version.lower()):
        if not token:
            continue
        if token.isdigit():
            values.append((0, int(token)))
        else:
            values.append((1, token))
    return values


def compare_versions(left: str, right: str) -> int:
    a = _tokenize(left)
    b = _tokenize(right)
    for index in range(max(len(a), len(b))):
        if index >= len(a):
            return -1
        if index >= len(b):
            return 1
        if a[index] == b[index]:
            continue
        if a[index][0] != b[index][0]:
            return -1 if a[index][0] < b[index][0] else 1
        return -1 if a[index][1] < b[index][1] else 1
    return 0


def version_matches_rule(
    version: str,
    *,
    exact: str | None = None,
    start_including: str | None = None,
    start_excluding: str | None = None,
    end_including: str | None = None,
    end_excluding: str | None = None,
) -> bool:
    if exact and exact not in {"*", "-"} and compare_versions(version, exact) != 0:
        return False
    if start_including and compare_versions(version, start_including) < 0:
        return False
    if start_excluding and compare_versions(version, start_excluding) <= 0:
        return False
    if end_including and compare_versions(version, end_including) > 0:
        return False
    if end_excluding and compare_versions(version, end_excluding) >= 0:
        return False
    return True


def evaluate_cpe_applicability(asset_cpe: str, rules: list[dict]) -> ApplicabilityResult:
    version = cpe_version(asset_cpe)
    if not version:
        return ApplicabilityResult("potentially_affected", 70, "CPE version could not be parsed.")

    matched = False
    evaluated = False

    for rule in rules:
        criteria = rule.get("criteria")
        if not criteria:
            continue

        criteria_parts = criteria.split(":")
        if len(criteria_parts) < 6:
            continue

        criteria_version = _cpe_unescape(criteria_parts[5])
        asset_parts = asset_cpe.split(":")
        if len(asset_parts) >= 6 and criteria_parts[:5] != asset_parts[:5]:
            continue

        evaluated = True
        in_range = version_matches_rule(
            version,
            exact=None if criteria_version in {"*", "-"} else criteria_version,
            start_including=rule.get("version_start_including"),
            start_excluding=rule.get("version_start_excluding"),
            end_including=rule.get("version_end_including"),
            end_excluding=rule.get("version_end_excluding"),
        )

        if in_range and rule.get("vulnerable", True):
            matched = True
        elif in_range and rule.get("vulnerable") is False:
            return ApplicabilityResult(
                "not_affected", 98, "NVD applicability rule explicitly marks the configuration as not vulnerable."
            )

    if matched:
        return ApplicabilityResult("confirmed_affected", 98, "Asset CPE and version matched an NVD vulnerable applicability rule.")
    if evaluated:
        return ApplicabilityResult("not_affected", 96, "NVD applicability rules were evaluated and the asset version did not match.")
    return ApplicabilityResult("potentially_affected", 75, "CPE matched the NVD result but no exact applicability rule could be evaluated.")
