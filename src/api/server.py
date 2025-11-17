from fastapi import FastAPI
from src.api.routes import settings as settings_routes
from src.api.routes import recordings as recordings_routes
from src.api.routes import system as system_routes

app = FastAPI(title="StreamRecorder API", version="0.2.0")

app.include_router(settings_routes.router)
app.include_router(recordings_routes.router)
app.include_router(system_routes.router)

# Recorder injection proxy

def set_recorder(recorder):
    recordings_routes.set_recorder(recorder)
