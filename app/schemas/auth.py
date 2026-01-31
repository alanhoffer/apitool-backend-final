from pydantic import BaseModel

class AuthData(BaseModel):
    user_id: int
    access_token: str

