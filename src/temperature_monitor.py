"""Temperature and Sensor Monitoring Module """

import subprocess
import platform
import re
import json
from rich.panel import Panel
from rich.table import Table
from rich import box

# Try to import py-smc for Apple Silicon
try:
    from smc import SMCConnection
    HAS_SMC = True
except ImportError:
    HAS_SMC = False


class TemperatureMonitor:
    """Monitor system temperatures and sensors (M3 Mac compatible)"""
    
    def __init__(self):
        self.temperatures = {}
        self.fan_speeds = {}
        self.power_info = {}
        self.thermal_pressure = None
        self.chip_type = self._detect_chip()
        self.supports_powermetrics = platform.system() == 'Darwin'
        self.smc = None
        
        if HAS_SMC:
            try:
                self.smc = SMCConnection()
            except Exception:
                pass
    
    def _detect_chip(self):
        """Detect if Mac is Apple Silicon or Intel"""
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                                  capture_output=True, text=True, timeout=1)
            if 'Apple' in result.stdout:
                # Try to get specific chip
                if 'M3' in result.stdout:
                    return 'M3'
                elif 'M2' in result.stdout:
                    return 'M2'
                elif 'M1' in result.stdout:
                    return 'M1'
                return 'Apple Silicon'
            return 'Intel'
        except Exception:
            return 'Unknown'
    
    def update(self):
        """Update temperature and sensor readings"""
        self.temperatures = {}
        self.fan_speeds = {}
        self.power_info = {}
        self.thermal_pressure = None
        
        # Method 1: Try SMC (most reliable for M3)
        if self.smc:
            self._get_smc_data()
        
        # Method 2: Try powermetrics (gives thermal pressure + power)
        if self.supports_powermetrics:
            self._get_powermetrics_data()
        
        # Method 3: Fallback to basic battery power
        if not self.power_info:
            self._get_battery_power()
    
    def _get_smc_data(self):
        """Get sensor data from SMC (Apple Silicon compatible)"""
        try:
            # Common SMC keys for temperature (vary by model)
            temp_keys = [
                'TC0P',  # CPU Proximity
                'TC0D',  # CPU Die
                'TC0E',  # CPU 1
                'TC0F',  # CPU 2
                'Tp0P',  # CPU Performance Core
                'Te0P',  # CPU Efficiency Core
                'TG0P',  # GPU Proximity
                'TG0D',  # GPU Die
                'TB0T',  # Battery
                'Ts0P',  # Palm Rest
                'TW0P',  # Airport (WiFi)
            ]
            
            sensor_names = {
                'TC0P': 'CPU Proximity',
                'TC0D': 'CPU Die',
                'TC0E': 'CPU Core 1',
                'TC0F': 'CPU Core 2',
                'Tp0P': 'CPU P-Core',
                'Te0P': 'CPU E-Core',
                'TG0P': 'GPU Proximity',
                'TG0D': 'GPU Die',
                'TB0T': 'Battery',
                'Ts0P': 'Palm Rest',
                'TW0P': 'WiFi',
            }
            
            for key in temp_keys:
                try:
                    value = self.smc.read_key(key)
                    if value and value > 0:
                        friendly_name = sensor_names.get(key, key)
                        self.temperatures[friendly_name] = value
                except Exception:
                    continue
            
            # Try to get fan speeds
            fan_keys = ['F0Ac', 'F1Ac']  # Actual fan speeds
            for i, key in enumerate(fan_keys):
                try:
                    rpm = self.smc.read_key(key)
                    if rpm and rpm > 0:
                        self.fan_speeds[f'Fan {i}'] = int(rpm)
                except Exception:
                    continue
                    
        except Exception as e:
            pass
    
    def _get_powermetrics_data(self):
        """Get power and thermal data from powermetrics (M3 compatible)"""
        try:
            # Run powermetrics for 1 sample
            result = subprocess.run(
                ['sudo', 'powermetrics', '--samplers', 'cpu_power,gpu_power,thermal', 
                 '-n', '1', '-i', '1000', '--format', 'plist'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode != 0:
                # Try without sudo (limited data)
                result = subprocess.run(
                    ['powermetrics', '--samplers', 'thermal', 
                     '-n', '1', '-i', '1000'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
            
            output = result.stdout
            
            # Parse thermal pressure
            match = re.search(r'thermal_pressure:\s*(\d+)', output)
            if match:
                self.thermal_pressure = int(match.group(1))
            
            # Parse CPU power
            match = re.search(r'CPU Power:\s*([\d.]+)\s*mW', output)
            if match:
                self.power_info['CPU'] = float(match.group(1)) / 1000  # Convert to Watts
            
            # Parse GPU power
            match = re.search(r'GPU Power:\s*([\d.]+)\s*mW', output)
            if match:
                self.power_info['GPU'] = float(match.group(1)) / 1000
            
            # Parse combined power
            match = re.search(r'Combined Power \(CPU \+ GPU\):\s*([\d.]+)\s*mW', output)
            if match:
                self.power_info['Total'] = float(match.group(1)) / 1000
                
        except Exception:
            pass
    
    def _get_battery_power(self):
        """Get basic power info from battery (fallback)"""
        try:
            result = subprocess.run(['pmset', '-g', 'batt'],
                                  capture_output=True, text=True, timeout=1)
            
            # Parse for wattage or current
            match = re.search(r'(\d+)W', result.stdout)
            if match:
                self.power_info['Battery Draw'] = float(match.group(1))
        except Exception:
            pass
    
    def get_info(self):
        """Get all sensor information as dictionary"""
        return {
            'temperatures': self.temperatures,
            'fans': self.fan_speeds,
            'power': self.power_info,
            'thermal_pressure': self.thermal_pressure
        }
    
    def get_panel(self) -> Panel:
        """Generate sensor panel"""
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Sensor", style="cyan", width=18)
        table.add_column("Value", style="green", width=20)
        
        if not self.temperatures and not self.fan_speeds and not self.power_info:
            self.update()
        
        # Show chip type
        table.add_row(
            "[bold]💻 Chip[/bold]",
            f"[cyan]{self.chip_type}[/cyan]"
        )
        
        # Thermal pressure (M3 specific)
        if self.thermal_pressure is not None:
            color = self._get_pressure_color(self.thermal_pressure)
            icon = self._get_pressure_icon(self.thermal_pressure)
            table.add_row(
                "[bold]🌡️  Thermal State[/bold]",
                f"[{color}]{icon} {self.thermal_pressure}%[/{color}]"
            )
            table.add_row("", "")  # Spacer
        
        # Temperature sensors
        if self.temperatures:
            table.add_row("[bold]🌡️  Temperatures[/bold]", "")
            for sensor, temp in sorted(self.temperatures.items()):
                color = self._get_temp_color(temp)
                icon = self._get_temp_icon(temp)
                table.add_row(
                    f"  {sensor}",
                    f"[{color}]{icon} {temp:.1f}°C[/{color}]"
                )
        
        # Fan speeds
        if self.fan_speeds:
            table.add_row("", "")  # Spacer
            table.add_row("[bold]💨 Fans[/bold]", "")
            for fan, rpm in sorted(self.fan_speeds.items()):
                color = self._get_fan_color(rpm)
                icon = self._get_fan_icon(rpm)
                table.add_row(
                    f"  {fan}",
                    f"[{color}]{icon} {rpm} RPM[/{color}]"
                )
        
        # Power consumption
        if self.power_info:
            table.add_row("", "")  # Spacer
            table.add_row("[bold]⚡ Power[/bold]", "")
            for component, watts in sorted(self.power_info.items()):
                color = self._get_power_color(watts)
                table.add_row(
                    f"  {component}",
                    f"[{color}]{watts:.2f} W[/{color}]"
                )
        
        # Show installation hint if no data
        if not self.temperatures and not self.fan_speeds and not self.power_info:
            table.add_row("", "")
            table.add_row(
                "[yellow]⚠️  Limited Data[/yellow]",
                ""
            )
            table.add_row(
                "[dim]Install:[/dim]",
                "[cyan]pip3 install py-smc[/cyan]"
            )
            table.add_row(
                "[dim]Or run:[/dim]",
                "[cyan]sudo python3 monitor.py[/cyan]"
            )
        
        title = f"[bold red]🌡️  Sensors ({self.chip_type})[/bold red]"
        
        return Panel(
            table,
            title=title,
            border_style="red",
            box=box.ROUNDED
        )
    
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
        if pressure < 25:
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
        if pressure < 25:
            return "✅"
        elif pressure < 50:
            return "⚠️"
        elif pressure < 75:
            return "🔥"
        else:
            return "🚨"
    
    @staticmethod
    def _get_fan_color(rpm):
        """Get color based on fan speed"""
        if rpm < 2000:
            return "green"
        elif rpm < 4000:
            return "yellow"
        elif rpm < 6000:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_fan_icon(rpm):
        """Get icon based on fan speed"""
        if rpm < 2000:
            return "💨"
        elif rpm < 4000:
            return "🌪️"
        else:
            return "🌀"
    
    @staticmethod
    def _get_power_color(watts):
        """Get color based on power consumption"""
        if watts < 10:
            return "green"
        elif watts < 20:
            return "yellow"
        elif watts < 30:
            return "orange1"
        else:
            return "red"
