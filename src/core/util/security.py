import os
import bcrypt
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from redis.asyncio import Redis

from src.database.Redisconfig import get_jwt_redis

load_dotenv()
ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALG = os.getenv("ALG")
ACCESS_EXP_TIME_MIN = int(os.getenv("ACCESS_EXP_TIME_MIN"))
REFRESH_EXP_TIME_DAY = int(os.getenv("REFRESH_EXP_TIME_DAY"))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authorization")


async def create_token(id:int):
    time = datetime.now()

    access_payload = {
        "sub":str(id),
        "exp":time + timedelta(minutes=ACCESS_EXP_TIME_MIN),
        "iat":time,
        "type":"access"
    }

    refresh_payload = {
            "sub":str(id),
            "exp":time + timedelta(minutes=REFRESH_EXP_TIME_DAY),
            "iat":time,
            "type":"refresh"
        }
    
    access_token = jwt.encode(
        access_payload, 
        ACCESS_SECRET_KEY, 
        algorithm=ALG
    )

    refresh_token = jwt.encode(
        refresh_payload, 
        REFRESH_SECRET_KEY, 
        algorithm=ALG
    )

    return access_token, refresh_token


async def upload_token(
    id:int, 
    access_token:str, 
    refresh_token:str, 
    db:Redis
):
    await db.set(
        f"whitelist_access_{access_token}", 
        str(id), 
        ex=ACCESS_EXP_TIME_MIN * 60
    )

    await db.set(
        f"refresh_token_{id}", 
        refresh_token, 
        ex=REFRESH_EXP_TIME_DAY * 24 * 3600
    )


async def block_token(
    access_token:str, 
    db:Redis
):
    if not await db.exists(f"whitelist_access_{access_token}"):
        raise HTTPException(
            detail="Invalid access token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    id = await db.get(f"whitelist_access_{access_token}")
    time = await db.ttl(f"whitelist_access_{access_token}")

    await db.set(f"blacklist_access_{access_token}", id, ex=time)

    await db.delete(f"whitelist_access_{access_token}")

    await db.delete(f"refresh_token_{id}")
   

async def refresh_tokens(
    refresh_token:str, 
    db:Redis
):
    try:
        payload = jwt.decode(
            refresh_token, 
            REFRESH_SECRET_KEY, 
            algorithms=ALG
        )

        id = payload.get("sub")

        exist_token = await db.get(f"refresh_token_{id}")

        if not exist_token:
            raise HTTPException(
                detail="Refresh token expired or logged out",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        if exist_token != refresh_token:
            await db.delete(f"refresh_token_{id}")
            raise HTTPException(
                detail="Token mismatch",
                status_code=status.HTTP_401_UNAUTHORIZED                
                )
        
        new_access, new_refresh = await create_token(id)

        await upload_token(id, new_access, new_refresh, db)

        return new_access, new_refresh
    except JWTError:
        raise HTTPException(
            detail="Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED           
        )


async def check_access_token(
    token:str = Depends(oauth2_scheme), 
    db:Redis = Depends(get_jwt_redis)
):
    if await db.exists(f"blacklist_access_{token}"):
        raise HTTPException(           
            detail="Access token expired or logged out",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    try:
        payload = jwt.decode(
            token, 
            ACCESS_SECRET_KEY, 
            algorithms=ALG
        )

        return payload
    except JWTError:
        raise HTTPException(
            detail="Invalid access token",
            status_code=status.HTTP_401_UNAUTHORIZED           
        )  


def encode_password(password:str):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')

def check_password(password:str, hashed_password:str):
    return bcrypt.checkpw(
        password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
    

# def get_role(allowed:list[str]):
#     async def _check(payload:dict = Depends(check_access_token)):
#         role = payload.get("role")
#         if role not in allowed:
#             raise HTTPException(
#                 detail="Do not have permission to access",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )
#         return role
#     return _check