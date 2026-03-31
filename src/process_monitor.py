"""Process Monitoring Module"""

import psutil
from rich.panel import Panel
from rich.table import Table
from rich import box


class ProcessMonitor:
    """Monitor running processes and resource usage"""
    
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.processes = []
    
    def update(self):
        """Update process list"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'] or 0,
                    'memory': pinfo['memory_percent'] or 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        self.processes = processes
    
    def get_panel(self) -> Panel:
        """Generate process panel with top processes"""
        if not self.processes:
            self.update()
        
        # Sort by CPU usage
        top_cpu = sorted(self.processes, key=lambda x: x['cpu'], reverse=True)[:self.top_n]
        
        table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        table.add_column("PID", style="cyan", justify="right", width=8)
        table.add_column("Process", style="white", no_wrap=True, width=25)
        table.add_column("CPU%", style="yellow", justify="right", width=8)
        table.add_column("MEM%", style="green", justify="right", width=8)
        
        for proc in top_cpu:
            cpu_color = self._get_color(proc['cpu'])
            mem_color = self._get_color(proc['memory'])
            
            # Truncate process name if too long
            name = proc['name'][:23] + '..' if len(proc['name']) > 25 else proc['name']
            
            table.add_row(
                str(proc['pid']),
                name,
                f"[{cpu_color}]{proc['cpu']:.1f}[/{cpu_color}]",
                f"[{mem_color}]{proc['memory']:.1f}[/{mem_color}]"
            )
        
        # Add summary
        total_processes = len(self.processes)
        
        return Panel(
            table,
            title=f"[bold white]⚡ Top Processes (Total: {total_processes})[/bold white]",
            border_style="white",
            box=box.ROUNDED
        )
    
    @staticmethod
    def _get_color(percent):
        """Get color based on usage percentage"""
        if percent < 25:
            return "green"
        elif percent < 50:
            return "yellow"
        elif percent < 75:
            return "orange1"
        else:
            return "red"
