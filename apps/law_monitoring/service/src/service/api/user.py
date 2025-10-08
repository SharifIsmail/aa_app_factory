from typing import Annotated

from fastapi import APIRouter, Depends

from service.core.dependencies.authorization import access_permission, with_user_profile
from service.core.services.auth_service import UserProfile

user_router = APIRouter(dependencies=[Depends(access_permission)])


@user_router.get("/user-profile")
async def user_profile(
    user_profile: Annotated[UserProfile, Depends(with_user_profile)],
) -> UserProfile:
    return user_profile
