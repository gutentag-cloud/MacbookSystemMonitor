"""Battery Monitoring Module"""

import psutil
from rich.panel import Panel
from rich.table import Table
from rich import box
from datetime import timedelta


class BatteryMonitor:
    """Monitor battery status and health"""
    
    def __init__(self):
        self.battery = None
        self.has_battery = True
    
    def update(self):
        """Update battery statistics"""
        try:
            self.battery = psutil.sensors_battery()
            if self.battery is None:
                self.has_battery = False
        except AttributeError:
            self.has_battery = False
    
    def get_panel(self) -> Panel:
        """Generate battery panel with statistics"""
        if not self.has_battery:
            return Panel(
                "[yellow]No battery detected or not supported[/yellow]",
                title="[bold yellow]🔋 Battery Monitor[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED
            )
        
        if not self.battery:
            self.update()
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Battery percentage
        percent = self.battery.percent
        color = self._get_color(percent, self.battery.power_plugged)
        icon = self._get_icon(percent, self.battery.power_plugged)
        
        table.add_row(
            "Charge Level",
            f"[{color}]{icon} {percent:.1f}%[/{color}]"
        )
        
        # Battery bar
        table.add_row(
            "Status",
            f"[{color}]{self._get_bar(percent)}[/{color}]"
        )
        
        # Power source
        if self.battery.power_plugged:
            table.add_row(
                "Power Source",
                "[green]⚡ AC Power (Charging)[/green]"
            )
        else:
            table.add_row(
                "Power Source",
                "[yellow]🔋 Battery[/yellow]"
            )
        
        # Time remaining
        if self.battery.secsleft != psutil.POWER_TIME_UNLIMITED and self.battery.secsleft != psutil.POWER_TIME_UNKNOWN:
            hours, remainder = divmod(self.battery.secsleft, 3600)
            minutes = remainder // 60
            
            if self.battery.power_plugged:
                table.add_row(
                    "Time to Full",
                    f"{int(hours)}h {int(minutes)}m"
                )
            else:
                table.add_row(
                    "Time Remaining",
                    f"{int(hours)}h {int(minutes)}m"
                )
        elif self.battery.power_plugged:
            if percent >= 99:
                table.add_row("Status", "[green]Fully Charged[/green]")
            else:
                table.add_row("Status", "[green]Charging[/green]")
        
        return Panel(
            table,
            title="[bold yellow]🔋 Battery Monitor[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _get_color(percent, plugged):
        """Get color based on battery percentage"""
        if plugged:
            return "green"
        elif percent > 50:
            return "green"
        elif percent > 20:
            return "yellow"
        else:
            return "red"
    
    @staticmethod
    def _get_icon(percent, plugged):
        """Get battery icon based on status"""
        if plugged:
            return "⚡"
        elif percent > 75:
            return "🔋"
        elif percent > 50:
            return "🔋"
        elif percent > 25:
            return "🪫"
        else:
            return "🪫"
    
    @staticmethod
    def _get_bar(percent, width=25):
        """Generate a battery bar"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percent:.1f}%"
