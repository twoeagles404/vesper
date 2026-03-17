from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Proxmox
    proxmox_host: str = "192.168.1.100"
    proxmox_port: int = 8006
    proxmox_user: str = "root@pam"
    proxmox_password: str = ""
    proxmox_verify_ssl: bool = False
    proxmox_node: str = "pve"

    # Weather (OpenWeatherMap)
    openweather_api_key: str = ""
    weather_city: str = "London"
    weather_units: str = "metric"  # metric or imperial

    # Calendar (iCal URL — no OAuth needed)
    ical_url: str = ""

    # RSS Feeds (comma-separated URLs)
    rss_feeds: str = ""

    # Service Health Checks (comma-separated Name=URL pairs)
    services: str = ""

    # Gmail OAuth2 (see .env.example for setup steps)
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
