from passlib.context import CryptContext

CRIPTO = CryptContext(schemes=["bcrypt"], deprecated="auto")

#verifica se a senha esta correta, comparaa com o texto puro informado pelo usuario e no hah
# da senha estara salvo no banco de datos durante a criacao da conta
def verify_password(plain_password, hashed_password) -> bool:
    return CRIPTO.verify(plain_password, hashed_password)

#retorna o hash da senha
def get_password_hash(password) -> str:
    return CRIPTO.hash(password)