"""Temperature and Sensor Monitoring Module"""

import subprocess
import platform
import re
import psutil
from rich.panel import Panel
from rich.table import Table
from rich import box


class TemperatureMonitor:
    """Monitor system temperatures and sensors (M3 Mac compatible)"""
    
    def __init__(self):
        self.temperatures = {}
        self.power_info = {}
        self.thermal_pressure = None
        self.chip_type = self._detect_chip()
        self.is_apple_silicon = 'Apple' in self.chip_type or 'M1' in self.chip_type or 'M2' in self.chip_type or 'M3' in self.chip_type
        self.cpu_count = psutil.cpu_count()
    
    def _detect_chip(self):
        """Detect if Mac is Apple Silicon or Intel"""
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=1)
            brand = result.stdout.strip()
            
            # Check for M-series chips
            if 'M3' in brand:
                # Detect variant
                if 'Max' in brand:
                    return 'M3 Max'
                elif 'Pro' in brand:
                    return 'M3 Pro'
                else:
                    return 'M3'
            elif 'M2' in brand:
                if 'Ultra' in brand:
                    return 'M2 Ultra'
                elif 'Max' in brand:
                    return 'M2 Max'
                elif 'Pro' in brand:
                    return 'M2 Pro'
                else:
                    return 'M2'
            elif 'M1' in brand:
                if 'Ultra' in brand:
                    return 'M1 Ultra'
                elif 'Max' in brand:
                    return 'M1 Max'
                elif 'Pro' in brand:
                    return 'M1 Pro'
                else:
                    return 'M1'
            elif 'Apple' in brand:
                return 'Apple Silicon'
            else:
                return brand[:30]  # Intel chip name
        except Exception:
            return 'Unknown'
    
    def update(self):
        """Update temperature and sensor readings"""
        self.temperatures = {}
        self.power_info = {}
        self.thermal_pressure = None
        
        if self.is_apple_silicon:
            # For Apple Silicon, use powermetrics and ioreg
            self._get_apple_silicon_data()
        else:
            # For Intel, try SMC tools if available
            self._get_intel_data()
        
        # Always try to get battery power (works on both)
        self._get_battery_power()
    
    def _get_apple_silicon_data(self):
        """Get thermal and power data for Apple Silicon (M1/M2/M3)"""
        
        # Method 1: Try powermetrics with sudo (best data)
        try:
            result = subprocess.run(
                ['sudo', '-n', 'powermetrics', '--samplers', 'cpu_power,gpu_power,thermal', 
                 '-n', '1', '-i', '1000'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                self._parse_powermetrics(result.stdout)
                return  # Got good data, we're done
        except Exception:
            pass
        
        # Method 2: Try without sudo (limited data, but something)
        try:
            result = subprocess.run(
                ['powermetrics', '--samplers', 'thermal', '-n', '1', '-i', '100'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                self._parse_powermetrics(result.stdout)
        except Exception:
            pass
        
        # Method 3: Try ioreg for thermal sensors
        try:
            result = subprocess.run(
                ['ioreg', '-n', 'AppleARMIODevice', '-r', '-d', '1'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                self._parse_ioreg_thermal(result.stdout)
        except Exception:
            pass
        
        # Method 4: Estimate from CPU frequency (fallback)
        if not self.temperatures:
            self._estimate_thermal_state()
    
    def _parse_powermetrics(self, output):
        """Parse powermetrics output for thermal and power data"""
        
        # Thermal pressure (0-100 scale)
        matches = re.findall(r'Thermal pressure:\s*(\d+)', output, re.IGNORECASE)
        if matches:
            self.thermal_pressure = int(matches[0])
        
        # CPU Power (in mW, convert to W)
        matches = re.findall(r'CPU Power:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['CPU'] = float(matches[0]) / 1000
        
        # GPU Power
        matches = re.findall(r'GPU Power:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['GPU'] = float(matches[0]) / 1000
        
        # ANE (Neural Engine) Power
        matches = re.findall(r'ANE Power:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['Neural Engine'] = float(matches[0]) / 1000
        
        # Combined Power
        matches = re.findall(r'Combined Power.*?:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['System'] = float(matches[0]) / 1000
        
        # E-Cluster (Efficiency cores)
        matches = re.findall(r'E-Cluster.*?:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['E-Cores'] = float(matches[0]) / 1000
        
        # P-Cluster (Performance cores)
        matches = re.findall(r'P-Cluster.*?:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['P-Cores'] = float(matches[0]) / 1000
    
    def _parse_ioreg_thermal(self, output):
        """Parse ioreg output for thermal data"""
        # This is a simplified parser - ioreg thermal data format varies
        matches = re.findall(r'"temperature"\s*=\s*(\d+)', output)
        if matches:
            # ioreg often reports in 1/100ths of degree
            temp = int(matches[0]) / 100.0
            if 20 < temp < 120:  # Sanity check
                self.temperatures['System'] = temp
    
    def _estimate_thermal_state(self):
        """Estimate thermal state from CPU usage (fallback)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Very rough estimation based on load
            if cpu_percent < 20:
                estimated_temp = 35 + (cpu_percent * 0.5)
                state = "Cool"
            elif cpu_percent < 50:
                estimated_temp = 45 + (cpu_percent * 0.4)
                state = "Normal"
            elif cpu_percent < 80:
                estimated_temp = 60 + (cpu_percent * 0.3)
                state = "Warm"
            else:
                estimated_temp = 70 + (cpu_percent * 0.2)
                state = "Hot"
            
            # Don't show estimated temps, just thermal state
            if not self.thermal_pressure:
                # Convert to thermal pressure equivalent
                self.thermal_pressure = int((estimated_temp - 30) * 1.5)
                
        except Exception:
            pass
    
    def _get_intel_data(self):
        """Get thermal data for Intel Macs"""
        # Try osx-cpu-temp if available
        try:
            result = subprocess.run(['osx-cpu-temp'],
                                  capture_output=True,
                                  text=True,
                                  timeout=1)
            if result.returncode == 0:
                match = re.search(r'([\d.]+)°?C', result.stdout)
                if match:
                    temp = float(match.group(1))
                    if temp > 0:
                        self.temperatures['CPU'] = temp
        except Exception:
            pass
        
        # Try istats if available
        try:
            result = subprocess.run(['istats', 'cpu', 'temp', '--no-graphs'],
                                  capture_output=True,
                                  text=True,
                                  timeout=1)
            if result.returncode == 0:
                match = re.search(r'([\d.]+)°C', result.stdout)
                if match:
                    temp = float(match.group(1))
                    if temp > 0:
                        self.temperatures['CPU'] = temp
        except Exception:
            pass
    
    def _get_battery_power(self):
        """Get power info from battery (works on all Macs)"""
        try:
            # Get battery info
            battery = psutil.sensors_battery()
            if battery:
                # Try to get power draw from pmset
                result = subprocess.run(['pmset', '-g', 'batt'],
                                      capture_output=True,
                                      text=True,
                                      timeout=1)
                
                if result.returncode == 0:
                    # Look for wattage
                    match = re.search(r'(\d+)W', result.stdout)
                    if match:
                        self.power_info['Battery'] = float(match.group(1))
                    
                    # Check if charging
                    if 'AC Power' in result.stdout or 'charging' in result.stdout.lower():
                        self.power_info['Status'] = 'Charging'
                    elif 'discharging' in result.stdout.lower():
                        self.power_info['Status'] = 'Discharging'
        except Exception:
            pass
    
    def get_info(self):
        """Get all sensor information as dictionary"""
        return {
            'temperatures': self.temperatures,
            'power': self.power_info,
            'thermal_pressure': self.thermal_pressure,
            'chip': self.chip_type
        }
    
    def get_panel(self) -> Panel:
        """Generate sensor panel"""
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Sensor", style="cyan", width=18)
        table.add_column("Value", style="green", width=22)
        
        if not self.temperatures and not self.power_info and self.thermal_pressure is None:
            self.update()
        
        # Show chip type
        table.add_row(
            "[bold]💻 Chip[/bold]",
            f"[cyan]{self.chip_type}[/cyan]"
        )
        
        # CPU Core count
        table.add_row(
            "[bold]🔢 Cores[/bold]",
            f"[cyan]{self.cpu_count}[/cyan]"
        )
        
        # Thermal pressure (Apple Silicon)
        if self.thermal_pressure is not None:
            color = self._get_pressure_color(self.thermal_pressure)
            icon = self._get_pressure_icon(self.thermal_pressure)
            state = self._get_thermal_state_name(self.thermal_pressure)
            table.add_row(
                "[bold]🌡️  Thermal State[/bold]",
                f"[{color}]{icon} {state} ({self.thermal_pressure}%)[/{color}]"
            )
        
        # Temperature sensors
        if self.temperatures:
            table.add_row("", "")  # Spacer
            table.add_row("[bold]🌡️  Temperatures[/bold]", "")
            for sensor, temp in sorted(self.temperatures.items()):
                color = self._get_temp_color(temp)
                icon = self._get_temp_icon(temp)
                table.add_row(
                    f"  {sensor}",
                    f"[{color}]{icon} {temp:.1f}°C[/{color}]"
                )
        
        # Power consumption
        if self.power_info:
            table.add_row("", "")  # Spacer
            table.add_row("[bold]⚡ Power[/bold]", "")
            
            # Separate status from power values
            status = self.power_info.pop('Status', None)
            
            for component, watts in sorted(self.power_info.items()):
                if isinstance(watts, (int, float)):
                    color = self._get_power_color(watts)
                    table.add_row(
                        f"  {component}",
                        f"[{color}]{watts:.2f} W[/{color}]"
                    )
            
            # Add status back if it existed
            if status:
                self.power_info['Status'] = status
                color = 'green' if status == 'Charging' else 'yellow'
                table.add_row(
                    f"  Battery Status",
                    f"[{color}]{status}[/{color}]"
                )
        
        # Show helpful message if limited data
        if not self.temperatures and not self.power_info:
            table.add_row("", "")
            table.add_row(
                "[yellow]⚠️  Limited Data[/yellow]",
                ""
            )
            table.add_row(
                "[dim]For full data:[/dim]",
                ""
            )
            table.add_row(
                "",
                "[cyan]sudo python3 monitor.py[/cyan]"
            )
        elif self.is_apple_silicon and not self.power_info:
            table.add_row("", "")
            table.add_row(
                "[dim]For power metrics:[/dim]",
                ""
            )
            table.add_row(
                "",
                "[cyan]sudo python3 monitor.py[/cyan]"
            )
        
        title = f"[bold red]🌡️  Sensors[/bold red]"
        
        return Panel(
            table,
            title=title,
            border_style="red",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _get_thermal_state_name(pressure):
        """Get thermal state name from pressure"""
        if pressure < 10:
            return "Nominal"
        elif pressure < 25:
            return "Cool"
        elif pressure < 50:
            return "Moderate"
        elif pressure < 75:
            return "Fair"
        elif pressure < 85:
            return "Heavy"
        else:
            return "Critical"
    
    @staticmethod
    def _get_temp_color(temp):
        """Get color based on temperature"""
        if temp < 45:
            return "cyan"
        elif temp < 60:
            return "green"
        elif temp < 75:
            return "yellow"
        elif temp < 85:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_temp_icon(temp):
        """Get icon based on temperature"""
        if temp < 50:
            return "❄️"
        elif temp < 70:
            return "🌡️"
        elif temp < 85:
            return "🔥"
        else:
            return "🚨"
    
    @staticmethod
    def _get_pressure_color(pressure):
        """Get color based on thermal pressure"""
        if pressure < 10:
            return "cyan"
        elif pressure < 25:
            return "green"
        elif pressure < 50:
            return "yellow"
        elif pressure < 75:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_pressure_icon(pressure):
        """Get icon based on thermal pressure"""
        if pressure < 10:
            return "❄️"
        elif pressure < 25:
            return "✅"
        elif pressure < 50:
            return "⚠️"
        elif pressure < 75:
            return "🔥"
        else:
            return "🚨"
    
    @staticmethod
    def _get_power_color(watts):
        """Get color based on power consumption"""
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
