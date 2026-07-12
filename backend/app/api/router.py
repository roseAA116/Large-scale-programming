from fastapi import APIRouter

from app.api.routes import admin, auth, chats, courses, dashboard, health, materials, plans, summaries, tasks, users

api_router = APIRouter()
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(chats.router)
api_router.include_router(courses.router)
api_router.include_router(dashboard.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(materials.router)
api_router.include_router(plans.router)
api_router.include_router(summaries.router)
api_router.include_router(tasks.router)
api_router.include_router(users.router)
