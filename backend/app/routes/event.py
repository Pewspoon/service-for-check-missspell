"""Роуты CRUD-операций для событий."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from database.create_tables import get_session
from models.event import Event, EventCreate
from typing import List, Dict


event_router = APIRouter()


@event_router.get(
    "/",
    response_model=list[Event]
)
async def retrieve_all_events(
    session: Session = Depends(get_session),
) -> list[Event]:
    """Получить список всех событий."""
    return list(session.exec(select(Event)).all())


@event_router.get(
    "/{id}",
    response_model=Event
)
async def retrieve_event(
    id: int,
    session: Session = Depends(get_session),
) -> Event:
    """Получить событие по его ID."""
    event = session.get(Event, id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event with supplied ID does not exist",
        )
    return event


@event_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    payload: EventCreate,
    session: Session = Depends(get_session),
) -> Dict:
    """Создать новое событие."""
    event = Event(**payload.model_dump())
    session.add(event)
    session.commit()
    session.refresh(event)
    return {"message": "Event created successfully", "id": event.id}


@event_router.delete(
    "/{id}"
)
async def delete_event(
    id: int,
    session: Session = Depends(get_session),
) -> Dict:
    """Удалить событие по его ID."""
    event = session.get(Event, id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event with supplied ID does not exist",
        )
    session.delete(event)
    session.commit()
    return {"message": "Event deleted successfully"}
