from fastapi import FastAPI
from api.chat import router as chat_router
from api.analytics import router as analytics_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Northstar AI",
    description="AI Sales Concierge for Northstar Homes",
    version="1.0.0",
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

app.include_router(
    chat_router,
    prefix="/api",
)



app.include_router(
    analytics_router,
    prefix="/api"
)


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Northstar AI Sales Concierge",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }