from fastapi import APIRouter, HTTPException, Depends, status

from sqlalchemy import select, and_, insert
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.routers.auth.security import *
from src.schemas.schem import UserCreate, UserResponse, UserShortResponse, UserUpdate, UserList

from src.database.DBconfig import get_db
from src.database.DBmodels import User, user_subscriptions


router = APIRouter(prefix="/users", tags=["Users api"])


@router.get("", response_model=UserList)
async def get_users(
    size:int,
    page:int,
    db:AsyncSession = Depends(get_db)
):
    users_query = await db.execute(
        select(User).
        order_by(User.id).
        limit(size).
        offset((page-1)*size).
        options(
            selectinload(User.subscriptions), 
            selectinload(User.subscribers)
        )
    )

    users = users_query.scalars().all()
    
    if not users:
        raise HTTPException(
            detail="Not found any available users", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    count = len(users)

    return {
        "count":count,
        "users":users
    }


@router.get("/{id}")
async def get_user(
    id:int, 
    payload:dict = Depends(check_access_token),
    db:AsyncSession = Depends(get_db)
):
    exist_user_query = await db.execute(
        select(User).
        where(User.id == id).
        options(
            selectinload(User.subscriptions), 
            selectinload(User.subscribers)
        )
    )
    
    exist_user = exist_user_query.scalars().first()

    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if id != int(payload.get("sub")):
        return UserShortResponse.model_validate(exist_user)
    
    return UserResponse.model_validate(exist_user)


@router.post("", response_model=UserResponse)
async def post_user(
    data:UserCreate, 
    db:AsyncSession = Depends(get_db)
):
    exist_user_query = await db.execute(
        select(User).
        where(
            User.name == data.name or 
            User.email == data.email
        )
    )
    
    exist_user = exist_user_query.scalars().first()

    if exist_user:
        raise HTTPException(
            detail="This user already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    payload = data.model_dump()
    payload["password"] = encode_password(data.password)

    new_user = User(**payload)
    new_user.subscriptions = []
    new_user.subscribers = []

    db.add(new_user)

    try:
        await db.commit()

        result = await db.execute(
            select(User)
            .where(User.id == new_user.id)
            .options(
                selectinload(User.subscriptions), 
                selectinload(User.subscribers)
            )
        )

        user = result.scalar_one()

        return user
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 


@router.put("", response_model=UserResponse)
async def put_user(
    id:int, 
    data:UserUpdate,
    payload:dict = Depends(check_access_token), 
    db:AsyncSession = Depends(get_db)
):
    if id != int(payload.get("sub")):
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )

    exist_user_query = await db.execute(
        select(User).
        where(User.id == id)
    )

    exist_user = exist_user_query.scalars().first()

    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )  
     
    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = encode_password(update_data["password"])

    for key, value in update_data.items():
        setattr(exist_user, key, value)

    try:
        await db.commit()
 
        query = await db.execute(
            select(User)
            .where(User.id == id)
            .options(
                selectinload(User.subscriptions), 
                selectinload(User.subscribers)
            )
        )

        user = query.scalar_one()

        return user
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 


@router.delete("")
async def delete_user(
    id:int, 
    payload:dict = Depends(check_access_token), 
    db:AsyncSession = Depends(get_db)
):
    if id != int(payload.get("sub")):
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )

    exist_user_query = await db.execute(
        select(User).
        where(User.id == id)
    )

    exist_user = exist_user_query.scalars().first()

    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    await db.delete(exist_user)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    
    return None


@router.post("/subscription", response_model=UserResponse)
async def user_subscribe(
    user_id:int, 
    author_id:int, 
    user_payload:dict = Depends(check_access_token),
    db:AsyncSession = Depends(get_db)
):
    if user_id != int(user_payload.get("sub")):
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )

    user_query = await db.execute(
        select(User).
        where(User.id == user_id)
    )

    author_query = await db.execute(
        select(User).
        where(User.id == author_id)
    )

    exist_user = user_query.scalars().first()

    exist_author = author_query.scalars().first()

    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if not exist_author:
        raise HTTPException(
            detail="Not found author with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    subscription_check = await db.execute(
        select(user_subscriptions).
        where(
            and_(
                user_subscriptions.c.subscriber_id == user_id,
                user_subscriptions.c.subscribed_to_id == author_id
            )
        )
    )

    if subscription_check.first():
        raise HTTPException(
            detail="Bad request, user already subscribed to this author",
            status_code=status.HTTP_400_BAD_REQUEST
        )  
      
    stmt = insert(user_subscriptions).values(
        subscriber_id=user_id,
        subscribed_to_id=author_id
    )

    try:
        await db.execute(stmt)
        await db.commit()
        
        query = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.subscriptions), 
                selectinload(User.subscribers)
            )
        )

        user = query.scalar_one()

        return user
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@router.delete("/subscription", response_model=UserResponse)
async def delete_subscribe(
    user_id:int, 
    author_id:int, 
    user_payload:dict = Depends(check_access_token),
    db:AsyncSession = Depends(get_db)
):  
    if user_id != int(user_payload.get("sub")) and author_id != int(user_payload.get("sub")):
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )

    user_query = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.subscribers))
    )

    author_query = await db.execute(
        select(User)
        .where(User.id == author_id)
        .options(selectinload(User.subscribers))
    )

    exist_user = user_query.scalars().first()
    
    exist_author = author_query.scalars().first()

    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if not exist_author:
        raise HTTPException(
            detail="Not found author with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if not (exist_user in exist_author.subscribers):
        raise HTTPException(
            detail="Bad request, user already subscribed to this author",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    exist_author.subscribers.remove(exist_user)
    
    try:
        await db.commit()
        
        query = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.subscriptions), 
                selectinload(User.subscribers)
            )
        )

        user = query.scalar_one()

        return user
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )