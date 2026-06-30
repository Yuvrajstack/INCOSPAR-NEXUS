import os

class Settings:
    PROJECT_NAME: str = "Incospar Nexus AI Backend"
    API_V1_STR: str = "/api"
    
    # SQLite Database Configuration
    DATABASE_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "incospar_telemetry.db"
    )
    
    @property
    def DATABASE_URL(self) -> str:
        db_dir = os.path.dirname(self.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Replace backslashes for sqlite windows path compatibility
        clean_path = self.DATABASE_PATH.replace("\\", "/")
        return f"sqlite:///{clean_path}"
    
    # Simulation Settings
    TELEMETRY_INTERVAL_SECONDS: float = 1.0
    NETFLOW_MAX_RECORDS: int = 1000
    SYSLOG_MAX_RECORDS: int = 1000
    HISTORY_RETENTION_SECONDS: int = 3600

settings = Settings()
