"""Disk Monitoring Module"""

import psutil
from rich.panel import Panel
from rich.table import Table
from rich import box


class DiskMonitor:
    """Monitor disk usage and I/O"""
    
    def __init__(self):
        self.partitions = []
        self.io_counters = None
        self.last_io = None
        self.read_speed = 0
        self.write_speed = 0
    
    def update(self):
        """Update disk statistics"""
        self.partitions = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        
        # I/O statistics
        current_io = psutil.disk_io_counters()
        if self.last_io:
            time_delta = 1  # Assuming 1 second interval
            self.read_speed = (current_io.read_bytes - self.last_io.read_bytes) / time_delta
            self.write_speed = (current_io.write_bytes - self.last_io.write_bytes) / time_delta
        self.last_io = current_io
    
    def get_panel(self) -> Panel:
        """Generate disk panel with statistics"""
        if not self.partitions:
            self.update()
        
        table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        table.add_column("Mount", style="cyan", no_wrap=True)
        table.add_column("Total", style="blue", justify="right")
        table.add_column("Used", style="yellow", justify="right")
        table.add_column("Free", style="green", justify="right")
        table.add_column("Usage", style="magenta")
        
        for partition in self.partitions:
            # Skip small or system partitions
            if partition['total'] < 1024 ** 3:  # Less than 1GB
                continue
            
            color = self._get_color(partition['percent'])
            
            table.add_row(
                partition['mountpoint'][:20],
                f"{self._bytes_to_gb(partition['total']):.1f}G",
                f"{self._bytes_to_gb(partition['used']):.1f}G",
                f"{self._bytes_to_gb(partition['free']):.1f}G",
                f"[{color}]{partition['percent']:.1f}%[/{color}]"
            )
        
        # Add I/O statistics
        if self.last_io:
            table.add_row("", "", "", "", "")  # Spacer
            table.add_row(
                "[bold]I/O Speed[/bold]",
                "",
                f"↓ {self._bytes_to_mb(self.read_speed):.1f} MB/s",
                f"↑ {self._bytes_to_mb(self.write_speed):.1f} MB/s",
                ""
            )
        
        return Panel(
            table,
            title="[bold cyan]💾 Disk Monitor[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _bytes_to_gb(bytes_val):
        """Convert bytes to gigabytes"""
        return bytes_val / (1024 ** 3)
    
    @staticmethod
    def _bytes_to_mb(bytes_val):
        """Convert bytes to megabytes"""
        return bytes_val / (1024 ** 2)
    
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
