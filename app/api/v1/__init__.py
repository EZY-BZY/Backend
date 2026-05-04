"""API v1 router - mounts active module routes."""

from fastapi import APIRouter

from app.modules.beasy_auth.routes import router as beasy_auth_router
from app.modules.beasy_employees.routes import router as employees_router
from app.modules.industries.routes_beasy import router as industries_beasy_router
from app.modules.industries.routes_global import router as industries_public_router
from app.modules.media.routes_beasy import router as media_beasy_router
from app.modules.terms.routes_beasy import router as terms_beasy_router
from app.modules.terms.routes_global import router as terms_public_router

api_router = APIRouter()

#--------------------------------beasy_router--------------------------------
# These are the routes that are shared by all Beasy employees
# example: Login to dashboard, CUD Terms
beasy_router = APIRouter(prefix="/beasy")
beasy_router.include_router(beasy_auth_router)
beasy_router.include_router(employees_router)
beasy_router.include_router(media_beasy_router)
beasy_router.include_router(industries_beasy_router)
beasy_router.include_router(terms_beasy_router)
# add routes to the action and ApiDocs
api_router.include_router(beasy_router)

#--------------------------------public_router--------------------------------
# These are the routes that are shared by all Beasy employees and clients
# example: View Terms
public_router = APIRouter(prefix="/public", tags=["Public Routes"])
public_router.include_router(industries_public_router)
public_router.include_router(terms_public_router)
api_router.include_router(public_router)

#--------------------------------clients_router--------------------------------
# These are the routes that are only for clients
# example: Create account, Business Account, etc.
clients_router = APIRouter(prefix="/clients", tags=["Clients Routes"])
# add routes to the action and ApiDocs
# api_router.include_router(clients_router)
