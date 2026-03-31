#!/usr/bin/env python3
"""
MacBook System Monitor - Main Entry Point
A comprehensive system monitoring tool for MacBook
"""

import sys
import time
import signal
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.cpu_monitor import CPUMonitor
from src.memory_monitor import MemoryMonitor
from src.disk_monitor import DiskMonitor
from src.network_monitor import NetworkMonitor
from src.battery_monitor import BatteryMonitor
from src.temperature_monitor import TemperatureMonitor
from src.process_monitor import ProcessMonitor


class SystemMonitor:
    """Main system monitor class that coordinates all sub-monitors"""
    
    def __init__(self, interval=1.0, minimal=False):
        self.console = Console()
        self.interval = interval
        self.minimal = minimal
        self.running = True
        self.paused = False
        
        # Initialize all monitors
        self.cpu = CPUMonitor()
        self.memory = MemoryMonitor()
        self.disk = DiskMonitor()
        self.network = NetworkMonitor()
        self.battery = BatteryMonitor()
        self.temperature = TemperatureMonitor()
        self.process = ProcessMonitor()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.running = False
    
    def create_layout(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="cpu"),
            Layout(name="memory"),
            Layout(name="network")
        )
        
        layout["right"].split_column(
            Layout(name="battery"),
            Layout(name="disk"),
            Layout(name="processes")
        )
        
        return layout
    
    def generate_header(self) -> Panel:
        """Generate the header panel"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
        
        grid.add_row(
            "🖥️  [bold cyan]MacBook System Monitor[/bold cyan]",
            f"[yellow]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]",
            "[green]Press 'q' to quit[/green]" if not self.paused else "[yellow]PAUSED[/yellow]"
        )
        
        return Panel(grid, style="white on blue", box=box.ROUNDED)
    
    def generate_footer(self) -> Panel:
        """Generate the footer panel"""
        shortcuts = (
            "[cyan]q[/cyan]:Quit  "
            "[cyan]p[/cyan]:Pause  "
            "[cyan]r[/cyan]:Reset  "
            "[cyan]s[/cyan]:Snapshot  "
            "[cyan]h[/cyan]:Help"
        )
        return Panel(shortcuts, style="white on blue", box=box.ROUNDED)
    
    def generate_dashboard(self) -> Layout:
        """Generate the complete dashboard"""
        layout = self.create_layout()
        
        # Update header and footer
        layout["header"].update(self.generate_header())
        layout["footer"].update(self.generate_footer())
        
        # Update all monitoring panels
        layout["cpu"].update(self.cpu.get_panel())
        layout["memory"].update(self.memory.get_panel())
        layout["disk"].update(self.disk.get_panel())
        layout["network"].update(self.network.get_panel())
        layout["battery"].update(self.battery.get_panel())
        layout["processes"].update(self.process.get_panel())
        
        # Add temperature info to CPU panel or separate if not minimal
        temp_info = self.temperature.get_info()
        if temp_info:
            layout["cpu"].update(self.cpu.get_panel(temp_info))
        
        return layout
    
    def run(self):
        """Main monitoring loop"""
        with Live(self.generate_dashboard(), refresh_per_second=4, screen=True) as live:
            while self.running:
                if not self.paused:
                    # Update all monitors
                    self.cpu.update()
                    self.memory.update()
                    self.disk.update()
                    self.network.update()
                    self.battery.update()
                    self.temperature.update()
                    self.process.update()
                    
                    # Update display
                    live.update(self.generate_dashboard())
                
                time.sleep(self.interval)
        
        self.console.print("\n[bold green]Monitoring stopped. Goodbye! 👋[/bold green]\n")


@click.command()
@click.option('--interval', '-i', default=1.0, help='Update interval in seconds', type=float)
@click.option('--minimal', '-m', is_flag=True, help='Minimal display mode')
@click.option('--export', '-e', default=None, help='Export data to JSON file', type=click.Path())
@click.version_option(version='1.0.0')
def main(interval, minimal, export):
    """
    MacBook System Monitor - Comprehensive system monitoring tool
    
    Monitor CPU, memory, disk, network, battery, and temperatures in real-time.
    """
    console = Console()
    
    # Display welcome message
    console.print("\n[bold cyan]🖥️  MacBook System Monitor[/bold cyan]", justify="center")
    console.print("[dim]Starting system monitoring...[/dim]\n", justify="center")
    
    try:
        monitor = SystemMonitor(interval=interval, minimal=minimal)
        monitor.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
