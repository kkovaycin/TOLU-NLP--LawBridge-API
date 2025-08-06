from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


# Access token (JWT) oluşturan fonksiyon
def create_access_token(data: dict, expires_delta: timedelta = None):
    # Gelen veriyi değiştirmemek için kopyalanır
    to_encode = data.copy()

    # Expire zamanı ayarlanır: Belirtilmişse onu, yoksa varsayılan süreyi kullan
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    # JWT standardına uygun olarak "exp" (expiration) eklenir
    to_encode.update({"exp": expire})

    # Token şifrelenerek oluşturulur
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    print("TOKEN PAYLOAD:", data)  # create_access_token içinde

    return encoded_jwt
