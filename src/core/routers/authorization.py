from fastapi import APIRouter, HTTPException, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..util.security import *
from ...database.DBmodels import User
from ...database.DBconfig import get_db


router = APIRouter(prefix="/authorization", tags=["Authorization api"])


@router.post("")
async def author_user(
    response:Response, 
    data:OAuth2PasswordRequestForm = Depends(), 
    db:AsyncSession = Depends(get_db), 
    redis:Redis = Depends(get_jwt_redis)
):
    user_query = await db.execute(
        select(User).
        where(User.email == data.username)
    )
    
    exist_user = user_query.scalars().first()

    if not exist_user:
        raise HTTPException(
            detail="Invalid email",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    if not check_password(data.password, exist_user.password):
        raise HTTPException(
            detail="inavlid password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    access_token, refresh_token = await create_token(exist_user.id)

    await upload_token(exist_user.id, access_token, refresh_token, redis)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=REFRESH_EXP_TIME_DAY * 24 * 3600
    )

    return {
        "access_token":access_token,
        "token_type": "bearer"
    }


@router.put("/refresh")
async def refresh_author(
    response:Response, 
    refresh_token:str = Cookie(None), 
    redis:Redis = Depends(get_jwt_redis)
):
    if not refresh_token:
        raise HTTPException(
            detail="Cant find refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    new_access, new_refresh = await refresh_tokens(refresh_token, redis)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        samesite="lax",
        max_age=REFRESH_EXP_TIME_DAY * 24 * 3600
    )

    return {
        "access_token":new_access
    }


@router.delete("/logout")
async def log_out_token(
    token:str = Depends(oauth2_scheme), 
    redis:Redis = Depends(get_jwt_redis)
):
    await block_token(token, redis)
    
    return None