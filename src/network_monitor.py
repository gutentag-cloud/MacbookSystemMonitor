"""Network Monitoring Module"""

import psutil
import time
from rich.panel import Panel
from rich.table import Table
from rich import box


class NetworkMonitor:
    """Monitor network usage and statistics"""
    
    def __init__(self):
        self.last_net_io = None
        self.upload_speed = 0
        self.download_speed = 0
        self.total_sent = 0
        self.total_recv = 0
        self.connections_count = 0
    
    def update(self):
        """Update network statistics"""
        current_net_io = psutil.net_io_counters()
        
        if self.last_net_io:
            time_delta = 1  # Assuming 1 second interval
            self.upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
            self.download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
        
        self.total_sent = current_net_io.bytes_sent
        self.total_recv = current_net_io.bytes_recv
        self.last_net_io = current_net_io
        
        # Count active connections
        try:
            self.connections_count = len(psutil.net_connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            self.connections_count = 0
    
    def get_panel(self) -> Panel:
        """Generate network panel with statistics"""
        if not self.last_net_io:
            self.update()
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Current speeds
        table.add_row("[bold]Current Speed[/bold]", "")
        table.add_row(
            "↓ Download",
            f"{self._format_speed(self.download_speed)}"
        )
        table.add_row(
            "↑ Upload",
            f"{self._format_speed(self.upload_speed)}"
        )
        
        # Total bandwidth
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Total Bandwidth[/bold]", "")
        table.add_row(
            "↓ Downloaded",
            f"{self._bytes_to_gb(self.total_recv):.2f} GB"
        )
        table.add_row(
            "↑ Uploaded",
            f"{self._bytes_to_gb(self.total_sent):.2f} GB"
        )
        
        # Connections
        table.add_row("", "")  # Spacer
        table.add_row(
            "Active Connections",
            f"{self.connections_count}"
        )
        
        # Network interfaces
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Interfaces[/bold]", "")
        
        for interface, stat in stats.items():
            if stat.isup and interface in addrs:
                status = "[green]UP[/green]" if stat.isup else "[red]DOWN[/red]"
                speed = f"{stat.speed} Mbps" if stat.speed > 0 else "N/A"
                table.add_row(
                    f"  {interface[:10]}",
                    f"{status} ({speed})"
                )
        
        return Panel(
            table,
            title="[bold green]🌐 Network Monitor[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _bytes_to_gb(bytes_val):
        """Convert bytes to gigabytes"""
        return bytes_val / (1024 ** 3)
    
    @staticmethod
    def _format_speed(bytes_per_sec):
        """Format speed in human-readable format"""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 ** 2:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1024 ** 3:
            return f"{bytes_per_sec / (1024 ** 2):.1f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 ** 3):.1f} GB/s"
