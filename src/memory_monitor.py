"""Memory Monitoring Module"""

import psutil
from rich.panel import Panel
from rich.table import Table
from rich import box


class MemoryMonitor:
    """Monitor memory and swap usage"""
    
    def __init__(self):
        self.memory = None
        self.swap = None
    
    def update(self):
        """Update memory statistics"""
        self.memory = psutil.virtual_memory()
        self.swap = psutil.swap_memory()
    
    def get_panel(self) -> Panel:
        """Generate memory panel with statistics"""
        if not self.memory:
            self.update()
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # RAM Information
        table.add_row("[bold]RAM[/bold]", "")
        table.add_row(
            "Total",
            f"{self._bytes_to_gb(self.memory.total):.2f} GB"
        )
        table.add_row(
            "Used",
            f"{self._bytes_to_gb(self.memory.used):.2f} GB "
            f"({self.memory.percent:.1f}%)"
        )
        table.add_row(
            "Available",
            f"{self._bytes_to_gb(self.memory.available):.2f} GB"
        )
        
        # Memory bar
        color = self._get_color(self.memory.percent)
        table.add_row(
            "Usage",
            f"[{color}]{self._get_bar(self.memory.percent)}[/{color}]"
        )
        
        # Swap Information
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Swap[/bold]", "")
        table.add_row(
            "Total",
            f"{self._bytes_to_gb(self.swap.total):.2f} GB"
        )
        table.add_row(
            "Used",
            f"{self._bytes_to_gb(self.swap.used):.2f} GB "
            f"({self.swap.percent:.1f}%)"
        )
        
        if self.swap.percent > 0:
            swap_color = self._get_color(self.swap.percent)
            table.add_row(
                "Usage",
                f"[{swap_color}]{self._get_bar(self.swap.percent)}[/{swap_color}]"
            )
        
        return Panel(
            table,
            title="[bold magenta]🧠 Memory Monitor[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _bytes_to_gb(bytes_val):
        """Convert bytes to gigabytes"""
        return bytes_val / (1024 ** 3)
    
    @staticmethod
    def _get_color(percent):
        """Get color based on usage percentage"""
        if percent < 50:
            return "green"
        elif percent < 75:
            return "yellow"
        elif percent < 90:
            return "orange1"
        else:
            return "red"
    
    @staticmethod
    def _get_bar(percent, width=25):
        """Generate a simple text progress bar"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percent:.1f}%"
