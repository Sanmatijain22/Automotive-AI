import asyncio
import datetime
import random
import uuid
from typing import List, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Machine, SensorReading, Alert, Prediction, SimulationSetting, MaintenanceTask, AutomotiveComponent
from app.services.anomaly_detection import anomaly_service
from app.services.failure_prediction import prediction_service
from app.services.maintenance_engine import maintenance_engine

INITIAL_MACHINES = [
    {"id":"VH-001","name":"Urban Hatchback","department":"Engine & Powertrain","model_number":"Generic Hatchback 2024","vehicle_category":"Hatchback","fuel_type":"Petrol","mileage":24500,"manufacturing_year":2024,"operating_hours":3420,"baseline_temp":92,"baseline_vib":1.8,"baseline_rpm":2400,"baseline_press":3.2,"baseline_power":18},
    {"id":"VH-002","name":"Executive Sedan","department":"Engine & Powertrain","model_number":"Generic Sedan 2023","vehicle_category":"Sedan","fuel_type":"Hybrid","mileage":42100,"manufacturing_year":2023,"operating_hours":5120,"baseline_temp":88,"baseline_vib":2.0,"baseline_rpm":2200,"baseline_press":3.1,"baseline_power":21},
    {"id":"VH-003","name":"Adventure SUV","department":"Chassis & Suspension","model_number":"Generic SUV 2025","vehicle_category":"SUV","fuel_type":"Diesel","mileage":18800,"manufacturing_year":2025,"operating_hours":2180,"baseline_temp":95,"baseline_vib":2.4,"baseline_rpm":2100,"baseline_press":3.4,"baseline_power":32},
    {"id":"VH-004","name":"City Electric","department":"Battery & Electrical","model_number":"Generic EV 2025","vehicle_category":"Electric Vehicle","fuel_type":"Electric","mileage":12850,"manufacturing_year":2025,"operating_hours":6250,"baseline_temp":72,"baseline_vib":1.2,"baseline_rpm":800,"baseline_press":12.4,"baseline_power":46},
    {"id":"VH-005","name":"Family Compact","department":"Braking & Safety","model_number":"Generic Hatchback 2022","vehicle_category":"Hatchback","fuel_type":"Petrol","mileage":68500,"manufacturing_year":2022,"operating_hours":1420,"baseline_temp":90,"baseline_vib":1.6,"baseline_rpm":1900,"baseline_press":3.0,"baseline_power":16},
    {"id":"VH-006","name":"Premium Sedan","department":"Cooling & Thermal","model_number":"Generic Sedan 2024","vehicle_category":"Sedan","fuel_type":"Petrol","mileage":31200,"manufacturing_year":2024,"operating_hours":3890,"baseline_temp":91,"baseline_vib":1.9,"baseline_rpm":2300,"baseline_press":3.3,"baseline_power":24},
    {"id":"VH-007","name":"Long-range SUV","department":"Tyres & Wheels","model_number":"Generic SUV 2023","vehicle_category":"SUV","fuel_type":"Hybrid","mileage":57900,"manufacturing_year":2023,"operating_hours":7820,"baseline_temp":94,"baseline_vib":2.2,"baseline_rpm":2050,"baseline_press":32.0,"baseline_power":28},
    {"id":"VH-008","name":"Urban Electric SUV","department":"Battery & Electrical","model_number":"Generic EV 2025","vehicle_category":"Electric Vehicle","fuel_type":"Electric","mileage":9200,"manufacturing_year":2025,"operating_hours":4310,"baseline_temp":70,"baseline_vib":1.1,"baseline_rpm":750,"baseline_press":12.6,"baseline_power":44},
]

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

connection_manager = ConnectionManager()

class SimulationEngine:
    def __init__(self):
        self.is_running = True
        self.task = None
        self.active_scenario = "NORMAL"
        self.injected_machine_id = "VH-001"
        self.fault_type = "engine_overheat"
        self.fault_step = 0
        self.max_fault_steps = 10

    def seed_database_if_needed(self):
        db: Session = SessionLocal()
        try:
            count = db.query(Machine).count()
            legacy_exists = db.query(Machine).filter(Machine.id.like("CNC-%")).first() is not None
            if count == 0 or legacy_exists:
                if legacy_exists:
                    print("Replacing legacy tractor/industrial records with automotive vehicle records...")
                    db.query(AutomotiveComponent).delete()
                    db.query(MaintenanceTask).delete()
                    db.query(Alert).delete()
                    db.query(Prediction).delete()
                    db.query(SensorReading).delete()
                    db.query(Machine).delete()
                    db.commit()
                print("Seeding 8 passenger cars into the automotive fleet...")
                now = datetime.datetime.utcnow()
                for data in INITIAL_MACHINES:
                    m = Machine(
                        id=data["id"],
                        name=data["name"],
                        department=data["department"],
                        model_number=data["model_number"],
                        installation_date=data.get("installation_date", "2024-01-15"),
                        operating_hours=data["operating_hours"],
                        status="healthy",
                        health_score=94.5,
                        anomaly_score=8.0,
                        failure_risk="Low Risk",
                        failure_probability=0.03,
                        current_temperature=data["baseline_temp"],
                        current_vibration=data["baseline_vib"],
                        current_rpm=data["baseline_rpm"],
                        current_pressure=data["baseline_press"],
                        current_power=data["baseline_power"],
                        vehicle_category=data["vehicle_category"],
                        fuel_type=data["fuel_type"],
                        mileage=data["mileage"],
                        manufacturing_year=data["manufacturing_year"],
                        baseline_temp=data["baseline_temp"],
                        baseline_vib=data["baseline_vib"],
                        baseline_rpm=data["baseline_rpm"],
                        baseline_press=data["baseline_press"],
                        baseline_power=data["baseline_power"],
                        last_maintenance=now - datetime.timedelta(days=random.randint(15, 60)),
                        next_scheduled_maintenance=now + datetime.timedelta(days=random.randint(20, 60)),
                    )
                    db.add(m)
                    
                    # Add initial baseline sensor history (15 points per machine)
                    for i in range(15, 0, -1):
                        past_time = now - datetime.timedelta(minutes=i * 2)
                        reading = SensorReading(
                            machine_id=data["id"],
                            timestamp=past_time,
                            temperature=round(data["baseline_temp"] + random.uniform(-1.5, 1.5), 1),
                            vibration=round(data["baseline_vib"] + random.uniform(-0.2, 0.2), 2),
                            rpm=round(data["baseline_rpm"] + random.uniform(-20, 20), 1),
                            pressure=round(data["baseline_press"] + random.uniform(-3, 3), 1),
                            power=round(data["baseline_power"] + random.uniform(-1, 1), 1),
                            operating_hours=round(data["operating_hours"] - (i * 0.03), 1),
                            anomaly_detected=False,
                            anomaly_score=round(random.uniform(5.0, 15.0), 1)
                        )
                        db.add(reading)

                    component_specs = [
                        ("Engine System", "Engine Assembly"),
                        ("Transmission System", "Transmission Assembly"),
                        ("Braking System", "Brake Assembly"),
                        ("Battery and Electrical", "Battery and Charging System"),
                        ("Suspension System", "Suspension Assembly"),
                        ("Cooling System", "Cooling Assembly"),
                        ("Tyre and Wheel System", "Tyre and Wheel Assembly"),
                    ]
                    for index, (category, name) in enumerate(component_specs, start=1):
                        db.add(AutomotiveComponent(
                            id=f"{data['id']}-CMP-{index:02d}",
                            vehicle_id=data["id"],
                            category=category,
                            name=name,
                            health_score=round(random.uniform(88.0, 98.0), 1),
                            operating_status="healthy",
                            failure_risk="Low Risk",
                            sensor_readings="{}",
                            maintenance_history="[]",
                        ))

                # Seed sample initial maintenance tasks
                task1 = MaintenanceTask(
                    id="MNT-101",
                    machine_id="VH-003",
                    title="Suspension and Shock Absorber Inspection",
                    description="Inspect suspension bushings, shock absorber condition, and wheel vibration.",
                    priority="MEDIUM",
                    status="UPCOMING",
                    category="Preventive",
                    scheduled_date=now + datetime.timedelta(days=3),
                    assigned_technician="Senior Automotive Technician",
                    estimated_hours=2.0
                )
                task2 = MaintenanceTask(
                    id="MNT-102",
                    machine_id="VH-007",
                    title="Tyre Pressure and Alignment Check",
                    description="Inspect tyre pressure, tread wear, wheel balance, and alignment.",
                    priority="LOW",
                    status="SCHEDULED",
                    category="Inspection",
                    scheduled_date=now + datetime.timedelta(days=7),
                    assigned_technician="Tyre Service Technician",
                    estimated_hours=1.5
                )
                db.add(task1)
                db.add(task2)
                
                db.commit()
                print("Database seeded successfully with 8 machines, sensor history, and maintenance tasks.")
        except Exception as e:
            db.rollback()
            print("Error seeding database:", e)
        finally:
            db.close()

    async def start(self):
        self.is_running = True
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._run_loop())
            print("Simulation loop started.")

    async def pause(self):
        self.is_running = False
        print("Simulation loop paused.")

    def set_scenario(self, scenario: str, machine_id: str = "VH-001", fault_type: str = "engine_overheat"):
        self.active_scenario = scenario
        self.injected_machine_id = machine_id
        self.fault_type = fault_type
        if scenario == "FAULT_INJECTION":
            self.fault_step = 1
        else:
            self.fault_step = 0

    async def _run_loop(self):
        while True:
            try:
                if self.is_running:
                    await self._tick()
            except Exception as e:
                print("Exception in simulation tick:", e)
            await asyncio.sleep(3.0)

    async def _tick(self):
        db: Session = SessionLocal()
        try:
            machines = db.query(Machine).all()
            if not machines:
                return

            now = datetime.datetime.utcnow()
            payload = []

            for m in machines:
                # Calculate new sensor readings with machine-specific bounds
                base_t = m.baseline_temp
                base_v = m.baseline_vib
                base_rpm = m.baseline_rpm
                base_p = m.baseline_press
                base_kw = m.baseline_power

                # Check if this machine is injected with fault in the scenario
                is_injected = (
                    self.active_scenario == "FAULT_INJECTION" 
                    and m.id == self.injected_machine_id
                )

                if is_injected:
                    self.fault_step = min(self.fault_step + 1, self.max_fault_steps)
                    severity_factor = self.fault_step / self.max_fault_steps # 0.1 to 1.0

                    if self.fault_type in ("bearing_and_thermal", "engine_overheat"):
                        # Engine overheating and abnormal vibration
                        new_t = base_t + (severity_factor * 33.0) + random.uniform(-1.0, 1.0) # Up to ~95°C
                        new_v = base_v + (severity_factor * 6.8) + random.uniform(-0.3, 0.4)  # Up to ~8.6 mm/s
                        new_rpm = base_rpm - (severity_factor * 250.0) + random.uniform(-15, 15)
                        new_p = base_p + random.uniform(-2, 2)
                        new_kw = base_kw + (severity_factor * 18.0) + random.uniform(-1, 1) # Overcurrent
                    elif self.fault_type in ("hydraulic_leak", "transmission_fault"):
                        # Transmission/gearbox pressure loss
                        new_t = base_t + (severity_factor * 18.0) + random.uniform(-1.0, 1.0)
                        new_v = base_v + (severity_factor * 2.5) + random.uniform(-0.2, 0.2)
                        new_rpm = base_rpm + random.uniform(-10, 10)
                        new_p = max(25.0, base_p - (severity_factor * 155.0) + random.uniform(-3, 3)) # Down to 55 bar
                        new_kw = base_kw + (severity_factor * 8.0)
                    else:
                        # Electrical overload
                        new_t = base_t + (severity_factor * 25.0)
                        new_v = base_v + (severity_factor * 3.5)
                        new_rpm = base_rpm - (severity_factor * 200.0)
                        new_p = base_p
                        new_kw = base_kw + (severity_factor * 28.0)
                else:
                    # Normal realistic bounded sensor jitter
                    new_t = base_t + random.uniform(-1.2, 1.2)
                    new_v = max(0.4, base_v + random.uniform(-0.15, 0.15))
                    new_rpm = max(100.0, base_rpm + random.uniform(-15.0, 15.0))
                    new_p = max(10.0, base_p + random.uniform(-2.5, 2.5))
                    new_kw = max(2.0, base_kw + random.uniform(-0.8, 0.8))

                new_t = round(float(new_t), 1)
                new_v = round(float(new_v), 2)
                new_rpm = round(float(new_rpm), 1)
                new_p = round(float(new_p), 1)
                new_kw = round(float(new_kw), 1)
                m.operating_hours = round(float(m.operating_hours + 0.005), 2)

                # Anomaly Detection & ML Prediction
                is_anomaly, anomaly_score = anomaly_service.detect(
                    new_t, new_v, new_rpm, new_p, new_kw, m.operating_hours
                )
                pred_result = prediction_service.predict(
                    new_t, new_v, new_rpm, new_p, new_kw, m.operating_hours
                )

                # Compute Health Score (100 - weighted risk & anomaly)
                health_score = round(max(5.0, min(100.0, 100.0 - (pred_result["risk_score"] * 0.7 + anomaly_score * 0.3))), 1)

                # Machine status
                if pred_result["failure_risk"] == "High Risk" or health_score < 45.0:
                    status = "critical"
                elif pred_result["failure_risk"] == "Medium Risk" or health_score < 75.0:
                    status = "warning"
                else:
                    status = "healthy"

                # Update Machine record
                m.current_temperature = new_t
                m.current_vibration = new_v
                m.current_rpm = new_rpm
                m.current_pressure = new_p
                m.current_power = new_kw
                m.health_score = health_score
                m.anomaly_score = anomaly_score
                m.failure_risk = pred_result["failure_risk"]
                m.failure_probability = pred_result["failure_probability"]
                m.status = status
                m.updated_at = now

                # Save SensorReading
                reading = SensorReading(
                    machine_id=m.id,
                    timestamp=now,
                    temperature=new_t,
                    vibration=new_v,
                    rpm=new_rpm,
                    pressure=new_p,
                    power=new_kw,
                    operating_hours=m.operating_hours,
                    anomaly_detected=is_anomaly,
                    anomaly_score=anomaly_score
                )
                db.add(reading)

                # Prune older readings if excessive (>120 per machine)
                excess_count = db.query(SensorReading).filter(SensorReading.machine_id == m.id).count()
                if excess_count > 120:
                    oldest_to_delete = db.query(SensorReading).filter(SensorReading.machine_id == m.id).order_by(SensorReading.timestamp.asc()).limit(20).all()
                    for old_r in oldest_to_delete:
                        db.delete(old_r)

                # Check Alert Generation
                if status in ["warning", "critical"]:
                    # Check if an unresolved alert already exists for this condition recently
                    existing_alert = db.query(Alert).filter(
                        Alert.machine_id == m.id,
                        Alert.resolved == False
                    ).first()

                    if not existing_alert:
                        severity = "CRITICAL" if status == "critical" else "MEDIUM"
                        rec = maintenance_engine.evaluate(new_t, new_v, new_rpm, new_p, new_kw, m.operating_hours, pred_result["failure_risk"])
                        
                        alert_id = f"ALT-{random.randint(1000, 9999)}"
                        if new_v >= 7.0:
                            anomaly_desc = "Critical Engine or Drivetrain Vibration"
                            detected_str = f"{new_v} mm/s"
                            thresh_str = "4.5 mm/s (ISO 10816)"
                        elif new_t >= 88.0:
                            anomaly_desc = "Thermal Overheat Runaway"
                            detected_str = f"{new_t} °C"
                            thresh_str = "80.0 °C"
                        elif new_p < 60.0:
                            anomaly_desc = "Severe Transmission Pressure Loss"
                            detected_str = f"{new_p} bar"
                            thresh_str = "80.0 bar"
                        else:
                            anomaly_desc = f"Sensor Anomaly Detected ({pred_result['failure_risk']})"
                            detected_str = f"Score: {anomaly_score}%"
                            thresh_str = "Nominal Profile"

                        new_alert = Alert(
                            id=alert_id,
                            machine_id=m.id,
                            timestamp=now,
                            severity=severity,
                            anomaly_type=anomaly_desc,
                            message=f"{m.name}: {anomaly_desc}. Sensor values indicate significant deviation from nominal baseline.",
                            detected_value=detected_str,
                            threshold_value=thresh_str,
                            recommended_action=rec["summary_recommendation"],
                            acknowledged=False,
                            resolved=False
                        )
                        db.add(new_alert)

                payload.append({
                    "id": m.id,
                    "name": m.name,
                    "department": m.department,
                    "temperature": new_t,
                    "vibration": new_v,
                    "rpm": new_rpm,
                    "pressure": new_p,
                    "power": new_kw,
                    "operating_hours": m.operating_hours,
                    "health_score": health_score,
                    "anomaly_score": anomaly_score,
                    "failure_risk": pred_result["failure_risk"],
                    "failure_probability": pred_result["failure_probability"],
                    "status": status,
                    "contributing_factors": pred_result["contributing_factors"],
                    "explanation": pred_result["explanation"]
                })

            db.commit()

            # Broadcast via WebSocket
            await connection_manager.broadcast({
                "type": "TELEMETRY_UPDATE",
                "timestamp": now.isoformat(),
                "machines": payload,
                "scenario": self.active_scenario
            })

        except Exception as e:
            db.rollback()
            print("Error in simulation tick execution:", e)
        finally:
            db.close()

simulation_engine = SimulationEngine()

