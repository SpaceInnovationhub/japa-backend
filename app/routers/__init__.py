# This file makes the routers directory a Python package
from .user import router as user_router
from .embassy import router as embassy_router
from .tickets import router as tickets_router
from .evacuation import router as evacuation_router

__all__ = ["user_router", "embassy_router", "tickets_router", "evacuation_router"]