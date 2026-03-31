"""CPU Monitoring Module"""

import psutil
from collections import deque
from rich.panel import Panel
from rich.table import Table
from rich.progress import BarColumn, Progress, TextColumn
from rich import box


class CPUMonitor:
    """Monitor CPU usage and statistics"""
    
    def __init__(self, history_length=60):
        self.history_length = history_length
        self.cpu_percent_history = deque(maxlen=history_length)
        self.per_cpu_history = []
        self.current_percent = 0
        self.per_cpu_percent = []
        self.cpu_freq = None
        self.load_avg = (0, 0, 0)
        self.cpu_count = psutil.cpu_count()
        
        # Initialize per-CPU history
        for _ in range(self.cpu_count):
            self.per_cpu_history.append(deque(maxlen=history_length))
    
    def update(self):
        """Update CPU statistics"""
        self.current_percent = psutil.cpu_percent(interval=0.1)
        self.per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        self.cpu_freq = psutil.cpu_freq()
        
        try:
            self.load_avg = psutil.getloadavg()
        except AttributeError:
            self.load_avg = (0, 0, 0)
        
        # Update history
        self.cpu_percent_history.append(self.current_percent)
        for i, percent in enumerate(self.per_cpu_percent):
            self.per_cpu_history[i].append(percent)
    
    def get_panel(self, temp_info=None) -> Panel:
        """Generate CPU panel with statistics"""
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Overall CPU usage
        color = self._get_color(self.current_percent)
        table.add_row(
            "Overall Usage",
            f"[{color}]{self.current_percent:.1f}%[/{color}] {self._get_bar(self.current_percent)}"
        )
        
        # CPU Frequency
        if self.cpu_freq:
            table.add_row(
                "Frequency",
                f"{self.cpu_freq.current:.0f} MHz"
            )
        
        # Load Average
        table.add_row(
            "Load Average",
            f"{self.load_avg[0]:.2f}, {self.load_avg[1]:.2f}, {self.load_avg[2]:.2f}"
        )
        
        # Temperature if available
        if temp_info and 'cpu' in temp_info:
            temp = temp_info['cpu']
            temp_color = self._get_temp_color(temp)
            table.add_row("Temperature", f"[{temp_color}]{temp:.1f}°C[/{temp_color}]")
        
        # Per-core usage
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Per-Core Usage[/bold]", "")
        
        for i, percent in enumerate(self.per_cpu_percent):
            color = self._get_color(percent)
            table.add_row(
                f"  Core {i}",
                f"[{color}]{percent:5.1f}%[/{color}] {self._get_bar(percent, width=15)}"
            )
        
        return Panel(
            table,
            title="[bold blue]🔥 CPU Monitor[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _get_color(percent):
        """Get color based on usage percentage"""
        if percent < 30:
            return "green"
        elif percent < 60:
            return "yellow"
        elif percent < 80:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_temp_color(temp):
        """Get color based on temperature"""
        if temp < 50:
            return "green"
        elif temp < 70:
            return "yellow"
        elif temp < 85:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_bar(percent, width=20):
        """Generate a simple text progress bar"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar
