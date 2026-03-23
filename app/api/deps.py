from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY
from app.models.user import User
from app.schemas.token import TokenPayload


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/access-token")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(sub=payload.get("sub"))
    except JWTError as exc:
        raise credentials_exception from exc

    if token_data.sub is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == token_data.sub))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
