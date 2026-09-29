from fastapi import APIRouter

from app.api.v1 import auth, results, rounds, scenarios, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(rounds.router)
api_router.include_router(scenarios.router)
api_router.include_router(results.router)
api_router.include_router(users.router)
