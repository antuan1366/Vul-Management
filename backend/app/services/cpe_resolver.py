import httpx


def resolve_cpe(
    *,
    url: str,
    vendor: str | None,
    product: str | None,
    model: str | None,
    version: str | None,
    timeout: int = 20,
    api_key: str | None = None,
) -> list[dict]:
    terms = [
        value.strip()
        for value in (vendor, product, model, version)
        if value and value.strip()
    ]

    if not terms:
        return []

    headers = {
        "User-Agent": "Vul-Management/1.1",
        "Accept": "application/json",
    }

    if api_key:
        headers["apiKey"] = api_key

    response = httpx.get(
        url,
        params={
            "keywordSearch": " ".join(terms),
            "resultsPerPage": 20,
        },
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()

    data = response.json()
    candidates = []

    for item in data.get("products", []):
        cpe = item.get("cpe", {})
        titles = cpe.get("titles") or []
        title = next(
            (
                entry.get("title")
                for entry in titles
                if entry.get("lang") == "en"
            ),
            titles[0].get("title") if titles else None,
        )

        cpe_names = cpe.get("cpeName") or []
        if isinstance(cpe_names, dict):
            cpe_names = [cpe_names]

        selected = next(
            (
                entry.get("cpeName")
                for entry in cpe_names
                if entry.get("cpeName")
            ),
            None,
        )

        candidates.append(
            {
                "cpe": selected,
                "title": title,
                "deprecated": cpe.get("deprecated", False),
                "deprecated_by": cpe.get("deprecatedBy"),
                "cpe_name_id": cpe.get("cpeNameId"),
            }
        )

    return candidates
