"""Temperature and Sensor Monitoring Module"""

import subprocess
import platform
import re
from rich.panel import Panel
from rich.table import Table
from rich import box


class TemperatureMonitor:
    """Monitor system temperatures and sensors"""
    
    def __init__(self):
        self.temperatures = {}
        self.fan_speeds = {}
        self.power_info = {}
        self.supports_temp = self._check_temp_support()
        self.supports_istats = self._check_istats_support()
        self.supports_powermetrics = self._check_powermetrics_support()
    
    def _check_temp_support(self):
        """Check if temperature monitoring is supported"""
        if platform.system() != 'Darwin':
            return False
        
        # Check if osx-cpu-temp is installed
        try:
            subprocess.run(['which', 'osx-cpu-temp'], 
                         capture_output=True, check=True, timeout=1)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def _check_istats_support(self):
        """Check if iStats is installed (for fan speeds and more sensors)"""
        if platform.system() != 'Darwin':
            return False
        
        try:
            subprocess.run(['which', 'istats'], 
                         capture_output=True, check=True, timeout=1)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def _check_powermetrics_support(self):
        """Check if powermetrics is available (built-in macOS)"""
        if platform.system() != 'Darwin':
            return False
        return True  # powermetrics is built into macOS
    
    def update(self):
        """Update temperature and sensor readings"""
        self.temperatures = {}
        self.fan_speeds = {}
        self.power_info = {}
        
        # Get basic CPU temperature
        if self.supports_temp:
            self._get_cpu_temp_basic()
        
        # Get detailed sensors from iStats
        if self.supports_istats:
            self._get_istats_data()
        
        # Get power metrics (requires sudo for detailed info)
        if self.supports_powermetrics:
            self._get_power_metrics()
    
    def _get_cpu_temp_basic(self):
        """Get CPU temperature using osx-cpu-temp"""
        try:
            result = subprocess.run(['osx-cpu-temp'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=1)
            
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                temp_value = float(temp_str.replace('°C', '').replace('°F', ''))
                self.temperatures['CPU'] = temp_value
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass
    
    def _get_istats_data(self):
        """Get detailed sensor data from iStats"""
        try:
            result = subprocess.run(['istats', '--no-graphs'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=2)
            
            if result.returncode == 0:
                self._parse_istats_output(result.stdout)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
    
    def _parse_istats_output(self, output):
        """Parse iStats output for various sensors"""
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # CPU temperature (multiple sensors)
            if 'CPU' in line and '°C' in line:
                match = re.search(r'CPU.*?:\s*([\d.]+)°C', line)
                if match:
                    temp = float(match.group(1))
                    # Extract specific CPU sensor name
                    sensor_match = re.search(r'(CPU[^:]*)', line)
                    sensor_name = sensor_match.group(1).strip() if sensor_match else 'CPU'
                    self.temperatures[sensor_name] = temp
            
            # GPU temperature
            if 'GPU' in line and '°C' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['GPU'] = float(match.group(1))
            
            # Battery temperature
            if 'Battery' in line and '°C' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['Battery'] = float(match.group(1))
            
            # SSD/Disk temperature
            if ('SSD' in line or 'Disk' in line or 'SMART' in line) and '°C' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['SSD'] = float(match.group(1))
            
            # Ambient temperature
            if 'Ambient' in line and '°C' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['Ambient'] = float(match.group(1))
            
            # Fan speeds
            if 'Fan' in line and 'RPM' in line:
                match = re.search(r'Fan.*?(\d+)\s*RPM', line)
                fan_num_match = re.search(r'Fan\s*(\d+)', line)
                if match:
                    rpm = int(match.group(1))
                    fan_num = fan_num_match.group(1) if fan_num_match else '0'
                    self.fan_speeds[f'Fan {fan_num}'] = rpm
            
            # Power/Wattage (if available)
            if 'Power' in line and 'W' in line:
                match = re.search(r'([\d.]+)\s*W', line)
                if match:
                    self.power_info['Power Draw'] = float(match.group(1))
    
    def _get_power_metrics(self):
        """Get power consumption data (basic, non-sudo version)"""
        try:
            # This is a simplified version that doesn't require sudo
            # For detailed metrics, user would need to run: sudo powermetrics -n 1
            result = subprocess.run(['pmset', '-g', 'batt'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=1)
            
            if result.returncode == 0:
                # Parse battery power info
                match = re.search(r'(\d+)W', result.stdout)
                if match:
                    self.power_info['Battery Power'] = float(match.group(1))
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
    
    def get_info(self):
        """Get all sensor information as dictionary"""
        return {
            'temperatures': self.temperatures,
            'fans': self.fan_speeds,
            'power': self.power_info
        }
    
    def get_panel(self) -> Panel:
        """Generate sensor panel"""
        if not self.supports_temp and not self.supports_istats:
            return Panel(
                "[yellow]⚠️  Advanced sensor monitoring not available[/yellow]\n\n"
                "[dim]Install monitoring tools:[/dim]\n"
                "[cyan]brew install osx-cpu-temp[/cyan]  (CPU temp)\n"
                "[cyan]brew install iStats[/cyan]        (All sensors)",
                title="[bold red]🌡️  Sensor Monitor[/bold red]",
                border_style="red",
                box=box.ROUNDED
            )
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Sensor", style="cyan", width=18)
        table.add_column("Value", style="green", width=15)
        
        if not self.temperatures and not self.fan_speeds:
            self.update()
        
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
            table.add_row("[bold]💨 Fan Speeds[/bold]", "")
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
            for metric, value in self.power_info.items():
                table.add_row(
                    f"  {metric}",
                    f"[yellow]{value:.1f} W[/yellow]"
                )
        
        if not self.temperatures and not self.fan_speeds and not self.power_info:
            table.add_row("[yellow]No sensor data available[/yellow]", "")
            table.add_row("[dim]Try: sudo python3 monitor.py[/dim]", "")
        
        return Panel(
            table,
            title="[bold red]🌡️  Sensor Monitor[/bold red]",
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
