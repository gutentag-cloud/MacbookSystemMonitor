"""Temperature Monitoring Module"""

import subprocess
import platform
from rich.panel import Panel
from rich.table import Table
from rich import box


class TemperatureMonitor:
    """Monitor system temperatures"""
    
    def __init__(self):
        self.temperatures = {}
        self.supports_temp = self._check_temp_support()
    
    def _check_temp_support(self):
        """Check if temperature monitoring is supported"""
        if platform.system() != 'Darwin':
            return False
        
        # Check if osx-cpu-temp is installed
        try:
            subprocess.run(['which', 'osx-cpu-temp'], 
                         capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def update(self):
        """Update temperature readings"""
        if not self.supports_temp:
            return
        
        try:
            # Get CPU temperature using osx-cpu-temp
            result = subprocess.run(['osx-cpu-temp'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=1)
            
            if result.returncode == 0:
                # Parse output (format: "XX.X°C")
                temp_str = result.stdout.strip()
                temp_value = float(temp_str.replace('°C', ''))
                self.temperatures['cpu'] = temp_value
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass
    
    def get_info(self):
        """Get temperature information as dictionary"""
        return self.temperatures
    
    def get_panel(self) -> Panel:
        """Generate temperature panel"""
        if not self.supports_temp:
            return Panel(
                "[yellow]Temperature monitoring not available[/yellow]\n"
                "[dim]Install with: brew install osx-cpu-temp[/dim]",
                title="[bold red]🌡️  Temperature Monitor[/bold red]",
                border_style="red",
                box=box.ROUNDED
            )
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Sensor", style="cyan")
        table.add_column("Temperature", style="green")
        
        if not self.temperatures:
            self.update()
        
        for sensor, temp in self.temperatures.items():
            color = self._get_color(temp)
            table.add_row(
                sensor.upper(),
                f"[{color}]{temp:.1f}°C[/{color}]"
            )
        
        if not self.temperatures:
            table.add_row("No Data", "[yellow]Unable to read temperatures[/yellow]")
        
        return Panel(
            table,
            title="[bold red]🌡️  Temperature Monitor[/bold red]",
            border_style="red",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _get_color(temp):
        """Get color based on temperature"""
        if temp < 50:
            return "green"
        elif temp < 70:
            return "yellow"
        elif temp < 85:
            return "orange1"
        else:
            return "red"
