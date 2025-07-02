from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    debug_mode: bool = False
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
# I am a backend developer with 4.5 years of experience in Python FastAPI.
# I am building this SAAS.
# so I am starting with backend first.
# So give the day wise task in very details for week 1.
# I can put about 1.5-2 hrs daily from mon-fri and on 5-6 on sat and sun.
