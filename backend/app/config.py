import os

class Settings:
    PROJECT_NAME: str = "AUTOMOTIVE AI – Smart Car Component Predictive Maintenance Intelligence System"
    PLANT: str = "PASSENGER-CAR-FLEET"
    DEPARTMENT: str = "Automotive Service Operations"
    SYSTEM_NAME: str = "Vehicle Component Health Monitoring"
    DATA_DISCLAIMER: str = "DEMO / SIMULATED DATA - Synthetic passenger-car telemetry for demonstration only"
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'smartmfg.db')}"
    )
    MODELS_DIR: str = os.path.join(BASE_DIR, "app", "ml", "saved_models")
    REPORTS_DIR: str = os.path.join(BASE_DIR, "reports_output")
    
    SIMULATION_INTERVAL: float = 3.0 # seconds between simulated sensor ticks

settings = Settings()
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
