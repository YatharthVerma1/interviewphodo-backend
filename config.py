from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    daily_api_key: str = ""
    daily_domain: str = ""
    google_api_key: str = ""
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "interviewphodo-storage"
    r2_endpoint: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "dev-secret-change-in-production"
    app_env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @staticmethod
    def _is_configured(value: str) -> bool:
        if not value or not value.strip():
            return False
        lower = value.lower()
        placeholders = ("your-", "your_", "change-me", "example.com", "placeholder")
        return not any(p in lower for p in placeholders)

    @property
    def supabase_configured(self) -> bool:
        return self._is_configured(self.supabase_url) and self._is_configured(
            self.supabase_service_key
        )

    @property
    def daily_configured(self) -> bool:
        return self._is_configured(self.daily_api_key)

    @property
    def google_configured(self) -> bool:
        return self._is_configured(self.google_api_key)

    @property
    def r2_configured(self) -> bool:
        return (
            self._is_configured(self.r2_access_key_id)
            and self._is_configured(self.r2_secret_access_key)
            and self._is_configured(self.r2_bucket_name)
            and self._is_configured(self.r2_endpoint)
        )

    @property
    def razorpay_configured(self) -> bool:
        return self._is_configured(self.razorpay_key_id) and self._is_configured(
            self.razorpay_key_secret
        )


settings = Settings()
