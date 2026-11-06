from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, ai, bookings, dashboard, errors, filters, uploads
from app.core.config import settings
from app.core.security import AccessControlMiddleware

app = FastAPI(title="Booking Analytics API", version="1.0.0")
app.add_middleware(AccessControlMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
for router in (uploads.router, dashboard.router, bookings.router, agents.router, errors.router, filters.router, ai.router):
    app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}



@app.get("/api/session")
def session():
    return {"authenticated": True}
