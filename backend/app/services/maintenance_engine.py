from typing import Dict, Any, List

class MaintenanceRecommendationEngine:
    @staticmethod
    def evaluate(temperature: float, vibration: float, rpm: float, pressure: float, power: float, operating_hours: float, failure_risk: str) -> Dict[str, Any]:
        recommendations = []
        priority = "LOW"
        tasks_suggested = []
        
        # Vibration Analysis
        if vibration >= 7.0:
            recommendations.append("Critical drivetrain vibration detected. Stop the vehicle if safe and inspect engine mounts, gearbox mounts, wheel balance, and bearing condition.")
            tasks_suggested.append("Emergency Drivetrain Inspection and Component Replacement")
            priority = "CRITICAL"
        elif vibration >= 4.0:
            recommendations.append("Elevated vibration observed. Inspect engine mounts, wheel balance, suspension bushings, and gearbox mounts.")
            tasks_suggested.append("Drivetrain and Suspension Vibration Inspection")
            if priority != "CRITICAL":
                priority = "HIGH"

        # Thermal Analysis
        if temperature >= 90.0:
            recommendations.append("Engine thermal risk. Check coolant level, radiator airflow, thermostat operation, cooling fan, and engine temperature sensor.")
            tasks_suggested.append("Cooling System Inspection and Engine Temperature Diagnosis")
            if priority not in ["CRITICAL"]:
                priority = "HIGH"
        elif temperature >= 78.0:
            recommendations.append("Operating temperature trending above normal. Inspect coolant level, radiator, hoses, fan operation, and thermostat.")
            tasks_suggested.append("Coolant System Inspection")
            if priority == "LOW":
                priority = "MEDIUM"

        # Pressure Analysis
        if pressure < 60.0:
            recommendations.append("Severe transmission pressure drop. Inspect transmission oil level, pump, pressure control valve, and hydraulic leaks.")
            tasks_suggested.append("Transmission Pressure and Oil Leak Inspection")
            if priority == "LOW":
                priority = "HIGH"
        elif pressure > 200.0:
            recommendations.append("Unusual pressure condition. Inspect pressure sensors and pressure-control components for restriction or calibration error.")
            tasks_suggested.append("Pressure Sensor and Control System Inspection")
            if priority == "LOW":
                priority = "MEDIUM"

        # Power Analysis
        if power > 50.0:
            recommendations.append("Abnormal electrical or charging load. Inspect battery connections, alternator output, accessory loading, and charging system.")
            tasks_suggested.append("Battery and Charging System Diagnostic")
            if priority == "LOW":
                priority = "MEDIUM"

        # Operating Hours Analysis
        if operating_hours > 7500.0:
            recommendations.append("Vehicle duty history indicates elevated wear. Schedule a comprehensive component inspection and fluid-service review.")
            tasks_suggested.append("High-Mileage Component Inspection")
            if priority == "LOW":
                priority = "MEDIUM"

        if not recommendations:
            recommendations.append("Machine parameters are well within standard operating limits. Continue routine daily autonomous maintenance (cleaning, lubrication, inspection).")
            tasks_suggested.append("Routine Autonomous Daily Inspection")
            priority = "LOW"

        # Combine priority with failure risk
        if failure_risk == "High Risk" and priority in ["LOW", "MEDIUM"]:
            priority = "HIGH"

        return {
            "priority": priority,
            "recommendations": recommendations,
            "tasks_suggested": tasks_suggested,
            "summary_recommendation": recommendations[0] if recommendations else "Nominal operating condition."
        }

maintenance_engine = MaintenanceRecommendationEngine()

