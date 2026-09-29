from fastapi import APIRouter, Depends, Response, status

from app.api.cookies import clear_auth_cookie, set_auth_cookie
from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import make_auth_limiter
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.schemas.errors import ErrorResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Separate counters so hammering /login doesn't block /register and vice versa.
register_limiter = make_auth_limiter()
login_limiter = make_auth_limiter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublic,
    dependencies=[Depends(register_limiter)],
    responses={409: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
def register(body: RegisterRequest, response: Response, db: DbSession) -> UserPublic:
    """Create an account and log in immediately (sets the auth cookie)."""
    user = auth_service.register_user(
        db,
        username=body.username,
        email=body.email,
        password=body.password.get_secret_value(),
    )
    set_auth_cookie(response, user.id)
    return UserPublic.model_validate(user)


@router.post(
    "/login",
    response_model=UserPublic,
    dependencies=[Depends(login_limiter)],
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
def login(body: LoginRequest, response: Response, db: DbSession) -> UserPublic:
    user = auth_service.authenticate(
        db, email=body.email, password=body.password.get_secret_value()
    )
    set_auth_cookie(response, user.id)
    return UserPublic.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_auth_cookie(response)


@router.get("/me", response_model=UserPublic, responses={401: {"model": ErrorResponse}})
def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)
