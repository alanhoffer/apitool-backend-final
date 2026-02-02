from app.config import settings

# JWT Configuration (from settings)
JWT_SECRET = settings.jwt_secret
BCRYPT_SALT_ROUNDS = settings.bcrypt_salt_rounds
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRATION_DAYS = settings.jwt_expiration_days

# Base URL
BASE_URL = settings.base_url
APIARY_IMG_URL = f"{BASE_URL}apiarys/profile/image/"

