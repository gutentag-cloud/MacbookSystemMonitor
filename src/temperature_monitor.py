"""Temperature and Sensor Monitoring Module - M3 Mac (Realistic)"""

import subprocess
import platform
import re
import psutil
from rich.panel import Panel
from rich.table import Table
from rich import box


class TemperatureMonitor:
    """Monitor system sensors (M3 Mac compatible - realistic version)"""
    
    def __init__(self):
        self.temperatures = {}
        self.power_info = {}
        self.thermal_pressure = None
        self.cpu_usage = 0
        self.chip_type = self._detect_chip()
        self.is_apple_silicon = 'M1' in self.chip_type or 'M2' in self.chip_type or 'M3' in self.chip_type or 'Apple' in self.chip_type
        self.cpu_count = psutil.cpu_count()
        self.battery_percent = None
        self.disk_read = 0
        self.disk_write = 0
        self.net_in = 0
        self.net_out = 0
    
    def _detect_chip(self):
        """Detect chip type"""
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=1)
            brand = result.stdout.strip()
            
            if 'M3' in brand:
                if 'Max' in brand:
                    return 'Apple M3 Max'
                elif 'Pro' in brand:
                    return 'Apple M3 Pro'
                else:
                    return 'Apple M3'
            elif 'M2' in brand:
                if 'Ultra' in brand:
                    return 'Apple M2 Ultra'
                elif 'Max' in brand:
                    return 'Apple M2 Max'
                elif 'Pro' in brand:
                    return 'Apple M2 Pro'
                else:
                    return 'Apple M2'
            elif 'M1' in brand:
                if 'Ultra' in brand:
                    return 'Apple M1 Ultra'
                elif 'Max' in brand:
                    return 'Apple M1 Max'
                elif 'Pro' in brand:
                    return 'Apple M1 Pro'
                else:
                    return 'Apple M1'
            elif 'Apple' in brand:
                return 'Apple Silicon'
            else:
                return brand[:25]
        except Exception:
            return 'Unknown'
    
    def update(self):
        """Update all sensor readings"""
        self.temperatures = {}
        self.power_info = {}
        self.thermal_pressure = None
        
        # Get CPU usage for thermal estimation
        self.cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Try to get actual temperature via ioreg
        self._get_ioreg_temps()
        
        # Get powermetrics data (battery, disk, network)
        self._get_powermetrics_data()
        
        # Get battery info
        self._get_battery_info()
        
        # Estimate thermal state from CPU usage if no direct reading
        if not self.temperatures:
            self._estimate_thermal()
    
    def _get_ioreg_temps(self):
        """Try to get temperatures from ioreg"""
        try:
            result = subprocess.run(
                ['ioreg', '-l'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Look for temperature values
                # Format varies: "temperature" = 12345 (in 1/100 or 1/256 degrees)
                temp_matches = re.findall(r'"temperature"\s*=\s*(\d+)', output)
                
                if temp_matches:
                    for i, match in enumerate(temp_matches[:5]):
                        raw_value = int(match)
                        
                        # Determine scale and convert
                        if raw_value > 25600:  # Likely 1/256 scale
                            temp = raw_value / 256.0
                        elif raw_value > 1000:  # Likely 1/100 scale  
                            temp = raw_value / 100.0
                        elif raw_value > 100:  # Likely 1/10 scale
                            temp = raw_value / 10.0
                        else:
                            temp = float(raw_value)
                        
                        # Sanity check for reasonable temps
                        if 15 < temp < 120:
                            sensor_name = ['SOC', 'CPU', 'GPU', 'PMU', 'Battery'][i] if i < 5 else f'Sensor {i}'
                            self.temperatures[sensor_name] = round(temp, 1)
                
                # Look for specific sensor patterns
                # AppleARMIODevice often has thermal data
                soc_temp = re.search(r'SOC.*?"temperature"\s*=\s*(\d+)', output, re.IGNORECASE | re.DOTALL)
                if soc_temp:
                    raw = int(soc_temp.group(1))
                    if raw > 1000:
                        self.temperatures['SOC'] = round(raw / 100.0, 1)
                    elif 20 < raw < 120:
                        self.temperatures['SOC'] = float(raw)
                        
        except Exception:
            pass
    
    def _get_powermetrics_data(self):
        """Get available data from powermetrics"""
        try:
            result = subprocess.run(
                ['sudo', '-n', 'powermetrics', '--samplers', 'cpu_power,gpu_power,thermal,disk,network', 
                 '-n', '1', '-i', '500'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                output = result.stdout
                self._parse_powermetrics(output)
        except Exception:
            pass
    
    def _parse_powermetrics(self, output):
        """Parse powermetrics output"""
        lines = output.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Thermal pressure
            if 'thermal pressure' in line_lower:
                match = re.search(r'(\d+)', line)
                if match:
                    self.thermal_pressure = int(match.group(1))
            
            # Battery percent
            if 'percent_charge' in line_lower:
                match = re.search(r'(\d+)', line)
                if match:
                    self.battery_percent = int(match.group(1))
            
            # CPU Power
            if 'cpu power' in line_lower and 'mw' in line_lower:
                match = re.search(r'([\d.]+)\s*mw', line_lower)
                if match:
                    self.power_info['CPU Power'] = round(float(match.group(1)) / 1000, 2)
            
            # GPU Power
            if 'gpu power' in line_lower and 'mw' in line_lower:
                match = re.search(r'([\d.]+)\s*mw', line_lower)
                if match:
                    self.power_info['GPU Power'] = round(float(match.group(1)) / 1000, 2)
            
            # Disk read
            if 'read:' in line_lower and 'kbytes' in line_lower:
                match = re.search(r'([\d.]+)\s*kbytes', line_lower)
                if match:
                    self.disk_read = round(float(match.group(1)) / 1024, 2)  # Convert to MB
            
            # Disk write
            if 'write:' in line_lower and 'kbytes' in line_lower:
                match = re.search(r'([\d.]+)\s*kbytes', line_lower)
                if match:
                    self.disk_write = round(float(match.group(1)) / 1024, 2)
            
            # Network in
            if 'in:' in line_lower and 'bytes/s' in line_lower:
                match = re.search(r'([\d.]+)\s*bytes/s', line_lower)
                if match:
                    self.net_in = round(float(match.group(1)) / 1024, 2)  # KB/s
            
            # Network out
            if 'out:' in line_lower and 'bytes/s' in line_lower:
                match = re.search(r'([\d.]+)\s*bytes/s', line_lower)
                if match:
                    self.net_out = round(float(match.group(1)) / 1024, 2)
    
    def _get_battery_info(self):
        """Get battery information"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                self.battery_percent = int(battery.percent)
                
                result = subprocess.run(['pmset', '-g', 'batt'],
                                      capture_output=True,
                                      text=True,
                                      timeout=1)
                
                if result.returncode == 0:
                    if 'AC Power' in result.stdout:
                        if 'charging' in result.stdout.lower():
                            self.power_info['Status'] = 'Charging'
                        elif battery.percent >= 99:
                            self.power_info['Status'] = 'Fully Charged'
                        else:
                            self.power_info['Status'] = 'Plugged In'
                    else:
                        self.power_info['Status'] = 'On Battery'
        except Exception:
            pass
    
    def _estimate_thermal(self):
        """Estimate thermal state from CPU usage"""
        # M3 chips are very efficient, estimate based on load
        if self.cpu_usage < 10:
            estimated_temp = 35 + (self.cpu_usage * 0.5)
            self.thermal_pressure = 5
        elif self.cpu_usage < 30:
            estimated_temp = 40 + (self.cpu_usage * 0.4)
            self.thermal_pressure = 15
        elif self.cpu_usage < 50:
            estimated_temp = 45 + (self.cpu_usage * 0.5)
            self.thermal_pressure = 30
        elif self.cpu_usage < 75:
            estimated_temp = 55 + (self.cpu_usage * 0.4)
            self.thermal_pressure = 50
        else:
            estimated_temp = 65 + (self.cpu_usage * 0.3)
            self.thermal_pressure = 70
        
        # Add estimated temp (clearly marked)
        self.temperatures['CPU (est.)'] = round(estimated_temp, 1)
    
    def get_info(self):
        """Get all sensor information"""
        return {
            'temperatures': self.temperatures,
            'power': self.power_info,
            'thermal_pressure': self.thermal_pressure,
            'chip': self.chip_type,
            'cpu_usage': self.cpu_usage,
            'battery': self.battery_percent
        }
    
    def get_panel(self) -> Panel:
        """Generate sensor panel"""
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=18)
        table.add_column("Value", style="green", width=25)
        
        if not self.temperatures and not self.power_info and self.thermal_pressure is None:
            self.update()
        
        # Chip info
        table.add_row(
            "[bold]💻 Chip[/bold]",
            f"[cyan]{self.chip_type}[/cyan]"
        )
        
        # Cores
        table.add_row(
            "[bold]🔢 CPU Cores[/bold]",
            f"[cyan]{self.cpu_count}[/cyan]"
        )
        
        # CPU Usage
        cpu_color = self._get_cpu_color(self.cpu_usage)
        table.add_row(
            "[bold]📊 CPU Usage[/bold]",
            f"[{cpu_color}]{self.cpu_usage:.1f}%[/{cpu_color}]"
        )
        
        # Thermal State
        if self.thermal_pressure is not None:
            color = self._get_pressure_color(self.thermal_pressure)
            icon = self._get_pressure_icon(self.thermal_pressure)
            state = self._get_thermal_state_name(self.thermal_pressure)
            table.add_row(
                "[bold]🌡️  Thermal State[/bold]",
                f"[{color}]{icon} {state}[/{color}]"
            )
        
        # Temperatures (if found)
        if self.temperatures:
            table.add_row("", "")
            table.add_row("[bold]🌡️  Temperatures[/bold]", "")
            
            for sensor, temp in sorted(self.temperatures.items()):
                color = self._get_temp_color(temp)
                icon = self._get_temp_icon(temp)
                # Mark estimated temps
                if 'est' in sensor.lower():
                    table.add_row(
                        f"  {sensor}",
                        f"[{color}]{icon} ~{temp:.1f}°C[/{color}] [dim](estimated)[/dim]"
                    )
                else:
                    table.add_row(
                        f"  {sensor}",
                        f"[{color}]{icon} {temp:.1f}°C[/{color}]"
                    )
        
        # Battery
        if self.battery_percent is not None:
            table.add_row("", "")
            table.add_row("[bold]🔋 Battery[/bold]", "")
            
            batt_color = self._get_battery_color(self.battery_percent)
            batt_icon = self._get_battery_icon(self.battery_percent, 'Status' in self.power_info and 'Charging' in self.power_info['Status'])
            table.add_row(
                f"  {batt_icon} Charge",
                f"[{batt_color}]{self.battery_percent}%[/{batt_color}]"
            )
            
            if 'Status' in self.power_info:
                status = self.power_info['Status']
                if 'Charging' in status:
                    s_color, s_icon = 'green', '⚡'
                elif 'Fully' in status:
                    s_color, s_icon = 'cyan', '✅'
                elif 'Plugged' in status:
                    s_color, s_icon = 'blue', '🔌'
                else:
                    s_color, s_icon = 'yellow', '🔋'
                
                table.add_row(
                    f"  {s_icon} Status",
                    f"[{s_color}]{status}[/{s_color}]"
                )
        
        # Power consumption
        power_items = {k: v for k, v in self.power_info.items() if k != 'Status' and isinstance(v, (int, float))}
        if power_items:
            table.add_row("", "")
            table.add_row("[bold]⚡ Power Draw[/bold]", "")
            
            for component, watts in sorted(power_items.items()):
                color = self._get_power_color(watts)
                table.add_row(
                    f"  {component}",
                    f"[{color}]{watts:.2f} W[/{color}]"
                )
        
        # Note about temperature on M3
        if self.is_apple_silicon and not any(k for k in self.temperatures if 'est' not in k.lower()):
            table.add_row("", "")
            table.add_row(
                "[dim]ℹ️  Note[/dim]",
                "[dim]M3 temps not exposed by Apple[/dim]"
            )
        
        return Panel(
            table,
            title="[bold red]🌡️  System Sensors[/bold red]",
            border_style="red",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _get_thermal_state_name(pressure):
        if pressure < 10:
            return "Nominal ❄️"
        elif pressure < 25:
            return "Cool ✅"
        elif pressure < 50:
            return "Moderate ⚠️"
        elif pressure < 75:
            return "Warm 🔥"
        else:
            return "Hot 🚨"
    
    @staticmethod
    def _get_temp_color(temp):
        if temp < 45:
            return "cyan"
        elif temp < 55:
            return "green"
        elif temp < 70:
            return "yellow"
        elif temp < 85:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_temp_icon(temp):
        if temp < 45:
            return "❄️"
        elif temp < 60:
            return "🌡️"
        elif temp < 80:
            return "🔥"
        else:
            return "🚨"
    
    @staticmethod
    def _get_pressure_color(pressure):
        if pressure < 15:
            return "cyan"
        elif pressure < 30:
            return "green"
        elif pressure < 50:
            return "yellow"
        elif pressure < 75:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_pressure_icon(pressure):
        if pressure < 15:
            return "❄️"
        elif pressure < 30:
            return "✅"
        elif pressure < 50:
            return "⚠️"
        elif pressure < 75:
            return "🔥"
        else:
            return "🚨"
    
    @staticmethod
    def _get_cpu_color(usage):
        if usage < 25:
            return "green"
        elif usage < 50:
            return "cyan"
        elif usage < 75:
            return "yellow"
        elif usage < 90:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_battery_color(percent):
        if percent > 80:
            return "green"
        elif percent > 50:
            return "cyan"
        elif percent > 20:
            return "yellow"
        else:
            return "red"
    
    @staticmethod
    def _get_battery_icon(percent, charging):
        if charging:
            return "⚡"
        elif percent > 80:
            return "🔋"
        elif percent > 50:
            return "🔋"
        elif percent > 20:
            return "🪫"
        else:
            return "🪫"
    
    @staticmethod
    def _get_power_color(watts):
        if watts < 5:
            return "green"
        elif watts < 15:
            return "cyan"
        elif watts < 25:
            return "yellow"
        elif watts < 40:
            return "orange1"
        else:
            return "red"
