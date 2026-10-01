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
        name = cpe.get("titles", [{}])[0].get("title")
        cpe_name = cpe.get("deprecatedBy") or cpe.get("cpeName")

        if isinstance(cpe_name, list):
            cpe_name = cpe_name[0].get("cpeName") if cpe_name else None

        candidates.append(
            {
                "cpe": cpe_name,
                "title": name,
                "deprecated": cpe.get("deprecated", False),
                "cpe_name_id": cpe.get("cpeNameId"),
            }
        )

    return candidates
