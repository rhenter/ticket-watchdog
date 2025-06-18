from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from starlette.middleware import Middleware

from src import crud, schemas, models
from src.config import start_config_watcher
from src.database import SessionLocal, engine, Base
from src.logging_middleware import StructuredLoggingMiddleware
from src.scheduler import start_scheduler
from src.ws import manager as ws_manager

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize configuration watcher and scheduler on startup
    start_config_watcher()
    start_scheduler()
    yield
    # Any shutdown cleanup would go here

middleware = [
    Middleware(StructuredLoggingMiddleware)
]
app = FastAPI(
    title="Ticket Watchdog",
    lifespan=lifespan,
    middleware=middleware,
)




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tickets", response_model=List[schemas.TicketSchema])
def ingest_ticket_batch(
        events: List[schemas.TicketEvent],
        db=Depends(get_db)
):
    """
    Ingest or update a batch of ticket events.
    """
    tickets = []
    for event in events:
        ticket = crud.update_ticket(db, event)
        tickets.append(ticket)
    return tickets


@app.get("/tickets/{ticket_id}", response_model=schemas.TicketSchema)
def get_ticket(ticket_id: str, db=Depends(get_db)):
    ticket = crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@app.get("/dashboard", response_model=List[schemas.TicketSchema])
def list_tickets(
    state: Optional[schemas.SLAState] = Query(
        None,
        description="Filter tickets by SLA state (ok, alert, breach)"
    ),
    offset: int = Query(0, ge=0, alias="offset"),
    limit: int = Query(100, ge=1, le=1000, alias="limit"),
    db = Depends(get_db)
):
    """
    List tickets with pagination using offset and limit.
    If `state` is provided, only tickets having at least one Alert
    with that SLAState will be returned.
    """
    query = db.query(models.Ticket)

    if state:
        query = (
            query
            .join(models.Alert)
            .filter(models.Alert.state == state)
            .distinct(models.Ticket.id)
        )

    tickets = query.offset(offset).limit(limit).all()
    return tickets


@app.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
