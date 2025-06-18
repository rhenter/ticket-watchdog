import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Union

from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, Body

from src import crud, schemas, models
from src.config import start_config_watcher
from src.database import SessionLocal, engine, Base
from src.logging_middleware import StructuredLoggingMiddleware
from src.scheduler import start_scheduler, evaluate_slas_for_ticket
from src.ws import manager

for logger_name in [
    "uvicorn.access",
    "uvicorn.error",
    "fastapi",
    "httpx",
    "urllib3",
    "starlette",
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the file‐watcher for sla_config.yaml
    start_config_watcher()
    # Start the background SLA evaluator
    start_scheduler()
    yield
    # (no teardown needed at the moment)


app = FastAPI(
    title="Ticket Watchdog",
    lifespan=lifespan
)
app.add_middleware(StructuredLoggingMiddleware)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tickets", response_model=List[schemas.TicketSchema])
async def ingest_ticket_events(
    events: Union[schemas.TicketEvent, List[schemas.TicketEvent]] = Body(...),
    db = Depends(get_db)
):
    # Normalize to list
    if isinstance(events, dict):
        events = [schemas.TicketEvent(**events)]
    elif isinstance(events, schemas.TicketEvent):
        events = [events]
    tickets = []
    for e in events:
        ticket = crud.update_ticket(db, e)
        tickets.append(ticket)
        evaluate_slas_for_ticket(ticket.id)
    return [schemas.TicketSchema.model_validate(t) for t in tickets]


@app.get("/tickets/{ticket_id}", response_model=schemas.TicketSchema)
async def get_ticket(ticket_id: str, db=Depends(get_db)):
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return schemas.TicketSchema.model_validate(ticket)


@app.get("/dashboard", response_model=List[schemas.TicketSchema])
async def list_tickets(
        state: Optional[schemas.SLAState] = Query(None),
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db=Depends(get_db)
):
    query = db.query(models.Ticket)

    if state is not None:
        # Convert Pydantic enum to SQLAlchemy enum
        model_state = models.SLAState(state.value)
        # If filtering for ALERT, include BREACH as well
        valid_states = [model_state]
        if model_state == models.SLAState.ALERT:
            valid_states.append(models.SLAState.BREACH)

        subq = (
            db.query(models.Alert.ticket_id)
            .filter(models.Alert.state.in_(valid_states))
        )
        query = query.filter(models.Ticket.id.in_(subq))

    tickets = query.offset(offset).limit(limit).all()
    return [schemas.TicketSchema.model_validate(t) for t in tickets]



@app.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Hold the connection open indefinitely
        await asyncio.Future()
    except WebSocketDisconnect:
        manager.disconnect(websocket)