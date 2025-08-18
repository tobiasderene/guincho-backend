from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.v1.endpoints import login_endpoints
import uvicorn
import logging


app = FastAPI(
    title="Guincho Backend",
    version="1.0.0"
)

# Configurar CORS para los frontends
origins = [
    "http://localhost:3000"                        # Solo para testing, podés limitar luego
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")
app.include_router(login_endpoints.router, prefix="/api/v1")

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port)
