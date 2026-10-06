from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feed import Feed
from app.schemas.feed import AUTH_TYPES, FEED_TYPES, METHODS, FeedCreate, FeedUpdate


DEFAULT_FEEDS = [
    {
        "name": "NVD CPE API",
        "feed_type": "nvd_cpe",
        "url": "https://services.nvd.nist.gov/rest/json/cpes/2.0",
        "method": "GET",
        "description": "NVD Official CPE Dictionary API used by Online CPE Check for Equipment, Operating Systems, and Applications.",
    },
    {
        "name": "NVD CVE API",
        "feed_type": "nvd_cve",
        "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
        "method": "GET",
        "description": "NVD CVE 2.0 API.",
    },
    {
        "name": "CISA KEV Catalog",
        "feed_type": "cisa_kev",
        "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "method": "GET",
        "description": "CISA Known Exploited Vulnerabilities Catalog JSON.",
    },
    {
        "name": "OSV API",
        "feed_type": "osv",
        "url": "https://api.osv.dev/v1/query",
        "method": "POST",
        "description": "OSV package query API used by Online PURL Check for Libraries.",
    },
]


def _validate_feed_data(feed_type: str, method: str, auth_type: str) -> None:
    if feed_type not in FEED_TYPES:
        raise ValueError(f"Unsupported feed type: {feed_type}.")
    if method not in METHODS:
        raise ValueError(f"Unsupported HTTP method: {method}.")
    if auth_type not in AUTH_TYPES:
        raise ValueError(f"Unsupported authentication type: {auth_type}.")


def serialize_feed(feed: Feed) -> dict:
    return {
        "id": feed.id,
        "name": feed.name,
        "feed_type": feed.feed_type,
        "url": feed.url,
        "method": feed.method,
        "enabled": feed.enabled,
        "auth_type": feed.auth_type,
        "has_api_key": bool(feed.api_key),
        "timeout_seconds": feed.timeout_seconds,
        "description": feed.description,
        "last_test_status": feed.last_test_status,
        "last_test_message": feed.last_test_message,
        "last_test_at": feed.last_test_at,
        "last_sync_at": feed.last_sync_at,
        "last_sync_status": feed.last_sync_status,
        "last_sync_message": feed.last_sync_message,
    }


def seed_default_feeds(db: Session) -> None:
    changed = False

    for definition in DEFAULT_FEEDS:
        existing = db.scalar(
            select(Feed).where(Feed.name == definition["name"])
        )
        if existing:
            continue

        db.add(Feed(**definition))
        changed = True

    if changed:
        db.commit()


def list_feeds(db: Session) -> list[dict]:
    feeds = db.scalars(select(Feed).order_by(Feed.id)).all()
    return [serialize_feed(feed) for feed in feeds]


def get_feed(db: Session, feed_id: int) -> Feed | None:
    return db.get(Feed, feed_id)


def create_feed(db: Session, data: FeedCreate) -> dict:
    _validate_feed_data(data.feed_type, data.method, data.auth_type)

    existing = db.scalar(select(Feed).where(Feed.name == data.name))
    if existing:
        raise ValueError("A feed with this name already exists.")

    feed = Feed(
        name=data.name,
        feed_type=data.feed_type,
        url=str(data.url),
        method=data.method,
        enabled=data.enabled,
        auth_type=data.auth_type,
        api_key=data.api_key,
        timeout_seconds=data.timeout_seconds,
        description=data.description,
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return serialize_feed(feed)


def update_feed(db: Session, feed: Feed, data: FeedUpdate) -> dict:
    values = data.model_dump(exclude_unset=True, exclude={"clear_api_key"})

    feed_type = values.get("feed_type", feed.feed_type)
    method = values.get("method", feed.method)
    auth_type = values.get("auth_type", feed.auth_type)
    _validate_feed_data(feed_type, method, auth_type)

    if "name" in values and values["name"] != feed.name:
        existing = db.scalar(
            select(Feed).where(
                Feed.name == values["name"],
                Feed.id != feed.id,
            )
        )
        if existing:
            raise ValueError("A feed with this name already exists.")

    if "url" in values and values["url"] is not None:
        values["url"] = str(values["url"])

    if data.clear_api_key:
        feed.api_key = None

    for key, value in values.items():
        setattr(feed, key, value)

    db.commit()
    db.refresh(feed)
    return serialize_feed(feed)


def delete_feed(db: Session, feed: Feed) -> None:
    db.delete(feed)
    db.commit()


def _request_kwargs(feed: Feed) -> dict:
    headers = {
        "User-Agent": "Vul-Management/2.0.1",
        "Accept": "application/json",
    }

    if feed.auth_type == "api_key" and feed.api_key:
        headers["apiKey"] = feed.api_key
    elif feed.auth_type == "bearer" and feed.api_key:
        headers["Authorization"] = f"Bearer {feed.api_key}"

    return {
        "headers": headers,
        "timeout": feed.timeout_seconds,
        "follow_redirects": True,
    }


def test_feed(db: Session, feed: Feed) -> dict:
    started = datetime.utcnow()

    try:
        with httpx.Client(**_request_kwargs(feed)) as client:
            if feed.feed_type == "osv" or feed.method == "POST":
                response = client.post(
                    feed.url,
                    json={
                        "package": {
                            "name": "jinja2",
                            "ecosystem": "PyPI",
                        },
                        "version": "3.1.0",
                    },
                )
            elif feed.feed_type == "nvd_cpe":
                response = client.get(
                    feed.url,
                    params={
                        "keywordSearch": "Cisco IOS XE",
                        "resultsPerPage": 1,
                    },
                )
            elif feed.feed_type == "nvd_cve":
                response = client.get(
                    feed.url,
                    params={"cveId": "CVE-2021-44228"},
                )
            else:
                response = client.get(feed.url)

        if response.is_success:
            message = f"Connection successful. HTTP {response.status_code}."
            status = "success"
        else:
            message = f"Endpoint returned HTTP {response.status_code}."
            status = "failed"

    except httpx.TimeoutException:
        status = "failed"
        message = "Connection timed out."
    except httpx.RequestError as error:
        status = "failed"
        message = f"Connection error: {error.__class__.__name__}."
    except Exception as error:
        status = "failed"
        message = f"Unexpected error: {error.__class__.__name__}."

    feed.last_test_status = status
    feed.last_test_message = message
    feed.last_test_at = started
    db.commit()
    db.refresh(feed)

    return serialize_feed(feed)
