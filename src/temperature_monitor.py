"""Temperature and Sensor Monitoring Module """

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
            # For Apple Silicon, use multiple methods to get actual temps
            self._get_apple_silicon_temps()
            self._get_apple_silicon_power()
        else:
            # For Intel, try SMC tools if available
            self._get_intel_data()
        
        # Always try to get battery power (works on both)
        self._get_battery_power()
    
    def _get_apple_silicon_temps(self):
        """Get actual CPU temperatures for Apple Silicon using multiple methods"""
        
        # Method 1: Try powermetrics with detailed temperature output
        try:
            result = subprocess.run(
                ['sudo', '-n', 'powermetrics', '--samplers', 'smc,cpu_power,gpu_power,thermal', 
                 '-n', '1', '-i', '1000'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                self._parse_powermetrics_temps(result.stdout)
        except Exception:
            pass
        
        # Method 2: Direct SMC key reading via sysctl (works on some M-series)
        if not self.temperatures:
            self._get_smc_via_sysctl()
        
        # Method 3: Try ioreg for thermal sensors
        if not self.temperatures:
            try:
                result = subprocess.run(
                    ['ioreg', '-l', '-w', '0'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    self._parse_ioreg_temps(result.stdout)
            except Exception:
                pass
        
        # Method 4: Try system_profiler for some thermal data
        if not self.temperatures:
            self._get_system_profiler_temps()
    
    def _get_apple_silicon_power(self):
        """Get power metrics for Apple Silicon"""
        try:
            result = subprocess.run(
                ['sudo', '-n', 'powermetrics', '--samplers', 'cpu_power,gpu_power,thermal', 
                 '-n', '1', '-i', '1000'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                self._parse_powermetrics_power(result.stdout)
                return
        except Exception:
            pass
        
        # Fallback: try without sudo (limited data)
        try:
            result = subprocess.run(
                ['powermetrics', '--samplers', 'thermal', '-n', '1', '-i', '100'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                self._parse_powermetrics_power(result.stdout)
        except Exception:
            pass
    
    def _parse_powermetrics_temps(self, output):
        """Parse powermetrics for temperature readings"""
        lines = output.split('\n')
        
        for line in lines:
            # Look for temperature readings in various formats
            
            # CPU die temperature
            if 'CPU die temperature' in line or 'cpu die temp' in line.lower():
                match = re.search(r'([\d.]+)\s*C', line)
                if match:
                    self.temperatures['CPU Die'] = float(match.group(1))
            
            # GPU temperature
            if 'GPU die temperature' in line or 'gpu die temp' in line.lower():
                match = re.search(r'([\d.]+)\s*C', line)
                if match:
                    self.temperatures['GPU Die'] = float(match.group(1))
            
            # Package temperature
            if 'package' in line.lower() and 'temp' in line.lower():
                match = re.search(r'([\d.]+)\s*C', line)
                if match:
                    self.temperatures['Package'] = float(match.group(1))
            
            # Performance cores temp
            if ('p-cluster' in line.lower() or 'pcluster' in line.lower()) and 'temp' in line.lower():
                match = re.search(r'([\d.]+)\s*C', line)
                if match:
                    self.temperatures['P-Cores'] = float(match.group(1))
            
            # Efficiency cores temp
            if ('e-cluster' in line.lower() or 'ecluster' in line.lower()) and 'temp' in line.lower():
                match = re.search(r'([\d.]+)\s*C', line)
                if match:
                    self.temperatures['E-Cores'] = float(match.group(1))
        
        # Also get thermal pressure
        match = re.search(r'Thermal pressure:\s*(\d+)', output, re.IGNORECASE)
        if match:
            self.thermal_pressure = int(match.group(1))
    
    def _parse_powermetrics_power(self, output):
        """Parse powermetrics output for power data"""
        
        # Thermal pressure
        match = re.search(r'Thermal pressure:\s*(\d+)', output, re.IGNORECASE)
        if match:
            self.thermal_pressure = int(match.group(1))
        
        # CPU Power
        matches = re.findall(r'CPU Power:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['CPU'] = float(matches[0]) / 1000
        
        # GPU Power
        matches = re.findall(r'GPU Power:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['GPU'] = float(matches[0]) / 1000
        
        # ANE Power
        matches = re.findall(r'ANE Power:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['Neural Engine'] = float(matches[0]) / 1000
        
        # E-Cluster
        matches = re.findall(r'E-Cluster.*?:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['E-Cores'] = float(matches[0]) / 1000
        
        # P-Cluster
        matches = re.findall(r'P-Cluster.*?:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['P-Cores'] = float(matches[0]) / 1000
        
        # Combined/System Power
        matches = re.findall(r'Combined Power.*?:\s*([\d.]+)\s*mW', output)
        if matches:
            self.power_info['System'] = float(matches[0]) / 1000
    
    def _get_smc_via_sysctl(self):
        """Try to get SMC temperatures via sysctl"""
        try:
            # Try to read thermal sensors via sysctl
            result = subprocess.run(
                ['sysctl', 'machdep.xcpm.cpu_thermal_level'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                # This gives thermal level, convert to approximate temp
                match = re.search(r':\s*(\d+)', result.stdout)
                if match:
                    thermal_level = int(match.group(1))
                    # Rough conversion: thermal_level to temperature
                    # Level 0 ≈ 40°C, increases ~5°C per level
                    approx_temp = 40 + (thermal_level * 5)
                    self.temperatures['CPU (estimated)'] = approx_temp
        except Exception:
            pass
    
    def _parse_ioreg_temps(self, output):
        """Parse ioreg output for temperature sensors"""
        # Look for AppleM[1-3]ScalarSensor or similar thermal sensors
        temp_pattern = r'"temperature"\s*=\s*(\d+)'
        matches = re.findall(temp_pattern, output)
        
        if matches:
            # ioreg typically reports in 1/256ths or 1/100ths of degree
            for i, match in enumerate(matches[:3]):  # Take first 3 sensors
                raw_value = int(match)
                
                # Try to determine the scale
                if raw_value > 10000:  # Likely in 1/256ths
                    temp = raw_value / 256.0
                elif raw_value > 1000:  # Likely in 1/100ths
                    temp = raw_value / 100.0
                else:
                    temp = float(raw_value)
                
                # Sanity check
                if 20 < temp < 120:
                    sensor_name = f'Sensor {i+1}' if i > 0 else 'CPU'
                    self.temperatures[sensor_name] = temp
    
    def _get_system_profiler_temps(self):
        """Get temperature info from system_profiler"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # This usually doesn't give temps directly, but we try
            # Most useful for confirming chip type
            pass
        except Exception:
            pass
    
    def _get_intel_data(self):
        """Get thermal data for Intel Macs"""
        # Try osx-cpu-temp
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
        
        # Try istats
        try:
            result = subprocess.run(['istats', '--no-graphs'],
                                  capture_output=True,
                                  text=True,
                                  timeout=1)
            if result.returncode == 0:
                self._parse_istats_output(result.stdout)
        except Exception:
            pass
    
    def _parse_istats_output(self, output):
        """Parse iStats output"""
        lines = output.split('\n')
        
        for line in lines:
            if 'CPU temp' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['CPU'] = float(match.group(1))
            elif 'GPU temp' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['GPU'] = float(match.group(1))
            elif 'Battery temp' in line:
                match = re.search(r'([\d.]+)°C', line)
                if match:
                    self.temperatures['Battery'] = float(match.group(1))
    
    def _get_battery_power(self):
        """Get power info from battery"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                result = subprocess.run(['pmset', '-g', 'batt'],
                                      capture_output=True,
                                      text=True,
                                      timeout=1)
                
                if result.returncode == 0:
                    # Look for wattage
                    match = re.search(r'(\d+)W', result.stdout)
                    if match:
                        self.power_info['Battery'] = float(match.group(1))
                    
                    # Check charging status
                    if 'AC Power' in result.stdout or 'AC attached' in result.stdout:
                        if 'charging' in result.stdout.lower():
                            self.power_info['Status'] = 'Charging'
                        elif battery.percent >= 99:
                            self.power_info['Status'] = 'Fully Charged'
                        else:
                            self.power_info['Status'] = 'Plugged In'
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
        table.add_column("Value", style="green", width=25)
        
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
        
        # Temperature sensors - SHOW THEM PROMINENTLY
        if self.temperatures:
            table.add_row("", "")  # Spacer
            table.add_row("[bold]🌡️  Temperatures[/bold]", "")
            
            # Sort to show most important temps first
            temp_order = ['CPU Die', 'CPU', 'Package', 'P-Cores', 'E-Cores', 'GPU Die', 'GPU', 'Battery']
            sorted_temps = {}
            
            # Add ordered temps
            for key in temp_order:
                if key in self.temperatures:
                    sorted_temps[key] = self.temperatures[key]
            
            # Add remaining temps
            for key, value in self.temperatures.items():
                if key not in sorted_temps:
                    sorted_temps[key] = value
            
            for sensor, temp in sorted_temps.items():
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
            
            # Show status first if it exists
            if 'Status' in self.power_info:
                status = self.power_info['Status']
                if 'Charging' in status:
                    color = 'green'
                    icon = '🔌'
                elif 'Fully Charged' in status:
                    color = 'cyan'
                    icon = '✅'
                elif 'Plugged In' in status:
                    color = 'blue'
                    icon = '🔌'
                elif 'Discharging' in status:
                    color = 'yellow'
                    icon = '🔋'
                else:
                    color = 'cyan'
                    icon = '⚡'
                table.add_row(
                    f"  {icon} Status",
                    f"[{color}]{status}[/{color}]"
                )
            
            # Show power values (skip Status)
            for component, value in sorted(self.power_info.items()):
                if component == 'Status':
                    continue
                
                if isinstance(value, (int, float)):
                    color = self._get_power_color(value)
                    table.add_row(
                        f"  {component}",
                        f"[{color}]{value:.2f} W[/{color}]"
                    )
        
        # Show helpful message if limited data
        if not self.temperatures and not self.power_info:
            table.add_row("", "")
            table.add_row(
                "[yellow]⚠️  Limited Sensor Data[/yellow]",
                ""
            )
            table.add_row(
                "[dim]For full metrics:[/dim]",
                ""
            )
            table.add_row(
                "",
                "[cyan]sudo python3 monitor.py[/cyan]"
            )
        elif self.is_apple_silicon and not self.temperatures:
            table.add_row("", "")
            table.add_row(
                "[yellow]⚠️  No temp sensors found[/yellow]",
                ""
            )
            table.add_row(
                "[dim]Run with sudo:[/dim]",
                ""
            )
            table.add_row(
                "",
                "[cyan]sudo python3 monitor.py[/cyan]"
            )
        elif self.is_apple_silicon and len(self.power_info) <= 2:
            table.add_row("", "")
            table.add_row(
                "[dim]💡 For detailed power:[/dim]",
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
