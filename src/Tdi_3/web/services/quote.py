def estimate_from_gcode(gcode_path, cost_per_m=0.2, cost_per_hour=10.0, kwh_rate=0.7, printer_watts=120):
    # Heurística mínima; substitua pelo parser do seu fatiador quando possível
    time_h = 1.5
    filament_m = 12.0
    energy_kwh = printer_watts/1000 * time_h
    total = filament_m*cost_per_m + time_h*cost_per_hour + energy_kwh*kwh_rate
    return {"time_h": time_h, "filament_m": filament_m, "energy_kwh": energy_kwh, "total": round(total,2)}
