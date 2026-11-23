# AUTOMOTIVE AI - Smart Car Component Predictive Maintenance Intelligence System

AI-powered passenger-vehicle component health monitoring, failure prediction, anomaly detection, and maintenance recommendations.

**Data disclaimer:** All fleet, sensor, prediction, and cost values are simulated demonstration data. The system does not use real vehicle telemetry or claim manufacturer affiliation or validation.

## Architecture

- React 19, Vite, TypeScript, Tailwind CSS, Recharts
- Python, FastAPI, SQLAlchemy, SQLite
- Scikit-learn Random Forest and Isolation Forest
- ReportLab PDF reports
- REST APIs and WebSocket telemetry

## Monitored Vehicle Fleet

The demo includes eight generic passenger vehicles:

- Hatchbacks
- Sedans
- SUVs
- Electric Vehicles

Vehicle records include vehicle ID, model, category, manufacturing year, fuel type, mileage, health score, and maintenance status.

## Component Architecture

1. Engine: temperature, RPM, oil pressure, vibration, coolant temperature
2. Transmission: gearbox temperature, oil pressure, gear-vibration, operating cycles
3. Braking: pad wear, disc temperature, brake pressure, vibration
4. Battery/Electrical: voltage, temperature, charging cycles, health
5. Suspension: vibration, shock condition, wheel vibration, stress
6. Cooling: coolant temperature, radiator performance, fan status
7. Tyres/Wheels: pressure, temperature, wheel vibration, wear

The existing SQLite `machines` table represents vehicles for backward-compatible APIs. The `automotive_components` table stores component records.

## Local Execution

Backend:

```powershell
cd backend
python -m pip install -r requirements.txt
python run.py
```

The API runs at `http://127.0.0.1:8000`; Swagger is at `/docs`.

Frontend development server:

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` or `VITE_API_BASE_URL` to the deployed backend URL. If unset, the frontend uses `http://127.0.0.1:8000`.

## API Endpoints

- `GET /api/health`
- `GET /api/dashboard/stats`
- `GET /api/machines` and `/api/vehicles`
- `GET /api/machines/{vehicle_id}`
- `GET /api/machines/{vehicle_id}/history`
- `GET /api/sensors/live`
- `GET /api/predictions`
- `POST /api/predictions/analyze`
- `GET /api/alerts`
- `GET /api/maintenance`
- `GET /api/reports/{vehicle_id}`
- `GET /api/components`

Existing `/api/machines` routes remain available for deployment compatibility.

## Machine Learning

The existing scaler, Random Forest, and Isolation Forest artifacts are retained. The scaler and model feature order is:

`temperature, vibration, rpm, pressure, power, operating_hours`

This pipeline is demonstration-oriented and must be retrained and validated with real, labeled passenger-car telemetry before operational use. No real-world accuracy or RUL claim is made.

## Build and Test

```powershell
cd frontend
npm run build

cd ..\backend
python test_app.py
```

## Deployment

- Render: deploy the Python backend, set `PORT` through the platform, and start `python run.py`.
- Vercel: deploy `frontend`, set `VITE_API_URL=https://<render-service>.onrender.com`, and verify CORS connectivity.
