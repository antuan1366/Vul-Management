from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.feed import FeedCreate, FeedResponse, FeedUpdate
from app.services.feeds import (
    create_feed,
    delete_feed,
    get_feed,
    list_feeds,
    test_feed,
    update_feed,
)


router = APIRouter(
    prefix="/api/feeds",
    tags=["Feeds"],
)


@router.get("", response_model=list[FeedResponse])
def list_feeds_api(db: Session = Depends(get_db)):
    return list_feeds(db)


@router.post("", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
def create_feed_api(data: FeedCreate, db: Session = Depends(get_db)):
    try:
        return create_feed(db, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.put("/{feed_id}", response_model=FeedResponse)
def update_feed_api(
    feed_id: int,
    data: FeedUpdate,
    db: Session = Depends(get_db),
):
    feed = get_feed(db, feed_id)
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found.",
        )

    try:
        return update_feed(db, feed, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feed_api(feed_id: int, db: Session = Depends(get_db)):
    feed = get_feed(db, feed_id)
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found.",
        )

    delete_feed(db, feed)


@router.post("/{feed_id}/test", response_model=FeedResponse)
def test_feed_api(feed_id: int, db: Session = Depends(get_db)):
    feed = get_feed(db, feed_id)
    if feed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found.",
        )

    return test_feed(db, feed)
