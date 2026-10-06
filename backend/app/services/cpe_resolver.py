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
        "User-Agent": "Vul-Management/2.0.1",
        "Accept": "application/json",
    }
    if api_key:
        headers["apiKey"] = api_key

    response = httpx.get(
        url,
        params={
            "keywordSearch": " ".join(terms),
            "resultsPerPage": 50,
        },
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()
    data = response.json()
    candidates = []

    for item in data.get("products", []):
        cpe = item.get("cpe", {}) or {}
        titles = cpe.get("titles") or []
        title = next(
            (entry.get("title") for entry in titles if entry.get("lang") == "en"),
            titles[0].get("title") if titles else None,
        )

        names = cpe.get("cpeName") or []
        if isinstance(names, dict):
            names = [names]

        selected = next(
            (entry.get("cpeName") for entry in names if entry.get("cpeName")),
            None,
        )
        if not selected:
            continue

        haystack = f"{selected} {title or ''}".lower()
        score = 0
        normalized = [value.lower().replace(" ", "_") for value in terms]

        for term in normalized:
            if term and term in haystack:
                score += 10

        if version and version.lower() in selected.lower():
            score += 35
        if model and model.lower().replace(" ", "_") in selected.lower():
            score += 20
        if product and product.lower().replace(" ", "_") in selected.lower():
            score += 15

        candidates.append(
            {
                "cpe": selected,
                "title": title,
                "deprecated": cpe.get("deprecated", False),
                "deprecated_by": cpe.get("deprecatedBy"),
                "cpe_name_id": cpe.get("cpeNameId"),
                "score": score,
            }
        )

    return sorted(
        candidates,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )
