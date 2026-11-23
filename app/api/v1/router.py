from fastapi import APIRouter
<<<<<<< HEAD

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router


api_router = APIRouter()

api_router = APIRouter()
=======
from app.api.v1.auth import router as auth_router
>>>>>>> 226ea8362b10b9740386248720ee8582d04b50cf

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)