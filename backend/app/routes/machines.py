from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Machine, SensorReading, Alert, MaintenanceTask, AutomotiveComponent
from app.schemas import MachineResponse, SensorReadingResponse
from app.services.maintenance_engine import maintenance_engine
from app.services.failure_prediction import prediction_service

router = APIRouter(prefix="/api/machines", tags=["Machines"])
vehicles_router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])
components_router = APIRouter(prefix="/api/components", tags=["Components"])

@router.get("", response_model=List[MachineResponse])
def get_machines(
    status: Optional[str] = Query("all", description="all, healthy, warning, critical"),
    search: Optional[str] = Query(None, description="Search by machine name or ID"),
    db: Session = Depends(get_db)
):
    query = db.query(Machine)
    
    if status and status.lower() != "all":
        query = query.filter(Machine.status == status.lower())
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Machine.id.ilike(search_filter)) | 
            (Machine.name.ilike(search_filter)) | 
            (Machine.department.ilike(search_filter))
        )
        
    machines = query.order_by(Machine.id.asc()).all()
    return [
        {
            **{column.name: getattr(machine, column.name) for column in Machine.__table__.columns},
            "vehicle_id": machine.id,
            "vehicle_model": machine.name,
            "maintenance_status": machine.status,
        }
        for machine in machines
    ]

@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine_detail(machine_id: str, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return {
        **{column.name: getattr(machine, column.name) for column in Machine.__table__.columns},
        "vehicle_id": machine.id,
        "vehicle_model": machine.name,
        "maintenance_status": machine.status,
    }

@router.get("/{machine_id}/history", response_model=List[SensorReadingResponse])
def get_machine_sensor_history(
    machine_id: str,
    limit: int = Query(60, ge=1, le=300),
    db: Session = Depends(get_db)
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
    readings = db.query(SensorReading)\
        .filter(SensorReading.machine_id == machine_id)\
        .order_by(SensorReading.timestamp.desc())\
        .limit(limit)\
        .all()
    # Return chronologically ascending for graphing
    return list(reversed(readings))

@router.get("/{machine_id}/recommendations")
def get_machine_recommendations(machine_id: str, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
    rec = maintenance_engine.evaluate(
        machine.current_temperature,
        machine.current_vibration,
        machine.current_rpm,
        machine.current_pressure,
        machine.current_power,
        machine.operating_hours,
        machine.failure_risk
    )
    
    pred = prediction_service.predict(
        machine.current_temperature,
        machine.current_vibration,
        machine.current_rpm,
        machine.current_pressure,
        machine.current_power,
        machine.operating_hours
    )
    
    return {
        "machine_id": machine.id,
        "machine_name": machine.name,
        "recommendations": rec,
        "prediction_breakdown": pred
    }

@vehicles_router.get("")
def get_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Machine).order_by(Machine.id.asc()).all()
    return [
        {
            "vehicle_id": vehicle.id,
            "vehicle_model": vehicle.name,
            "vehicle_category": vehicle.vehicle_category,
            "manufacturing_year": vehicle.manufacturing_year,
            "fuel_type": vehicle.fuel_type,
            "mileage": vehicle.mileage,
            "vehicle_health_score": vehicle.health_score,
            "component_health_summary": vehicle.component_health_summary,
            "maintenance_status": vehicle.status,
        }
        for vehicle in vehicles
    ]

@vehicles_router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Machine).filter(Machine.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return {
        "vehicle_id": vehicle.id,
        "vehicle_model": vehicle.name,
        "vehicle_category": vehicle.vehicle_category,
        "manufacturing_year": vehicle.manufacturing_year,
        "fuel_type": vehicle.fuel_type,
        "mileage": vehicle.mileage,
        "vehicle_health_score": vehicle.health_score,
        "component_health_summary": vehicle.component_health_summary,
        "maintenance_status": vehicle.status,
    }

@components_router.get("")
def get_components(vehicle_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AutomotiveComponent)
    if vehicle_id:
        query = query.filter(AutomotiveComponent.vehicle_id == vehicle_id)
    components = query.all()
    return [
        {
            "component_id": component.id,
            "component_name": component.name,
            "vehicle_id": component.vehicle_id,
            "category": component.category,
            "health_score": component.health_score,
            "operating_status": component.operating_status,
            "failure_risk": component.failure_risk,
            "sensor_readings": component.sensor_readings,
            "maintenance_history": component.maintenance_history,
        }
        for component in components
    ]

