from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    auth0_domain: str
    auth0_audience: str

    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.auth0_domain}/"

    @property
    def auth0_jwks_uri(self) -> str:
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "env_file_required": False}


settings = Settings()
