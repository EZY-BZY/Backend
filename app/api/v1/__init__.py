"""API v1 router - mounts active module routes."""

from fastapi import APIRouter

from app.modules.beasy_auth.routes import router as beasy_auth_router
from app.modules.beasy_employees.routes import router as employees_router

api_router = APIRouter()

#--------------------------------beasy_router--------------------------------
# These are the routes that are shared by all Beasy employees
# example: Login to dashboard, CUD Terms
beasy_router = APIRouter(prefix="/beasy")
beasy_router.include_router(beasy_auth_router)
beasy_router.include_router(employees_router)
# add routes to the action and ApiDocs
api_router.include_router(beasy_router)

#--------------------------------global_router--------------------------------
# These are the routes that are shared by all Beasy employees and clients
# example: View Terms
global_router = APIRouter(prefix="/global", tags=["Global Routes"])
# global_router.include_router()
# api_router.include_router(global_router)

#--------------------------------clients_router--------------------------------
# These are the routes that are only for clients
# example: Create account, Business Account, etc.
clients_router = APIRouter(prefix="/clients", tags=["Clients Routes"])
# add routes to the action and ApiDocs
# api_router.include_router(clients_router)
