from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.password_reset import router as password_reset_router
from app.api.v1 import membresias
<<<<<<< HEAD
from app.api.v1 import profile
from app.api.v1 import progress
=======
>>>>>>> origin/master
from app.api.v1 import ejercicios
from app.api.v1 import alimentos

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(password_reset_router)
api_router.include_router(membresias.router)
<<<<<<< HEAD
api_router.include_router(profile.router)
api_router.include_router(progress.router)
=======
>>>>>>> origin/master
api_router.include_router(ejercicios.router)
api_router.include_router(alimentos.router)