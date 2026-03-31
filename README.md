# 🖥️ MacBook System Monitor

A comprehensive, real-time system monitoring tool for MacBook with a beautiful terminal interface.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 📊 **CPU Monitoring**: Real-time CPU usage per core with history graph
- 🧠 **Memory Tracking**: RAM and swap usage with detailed breakdowns
- 💾 **Disk Usage**: Monitor all mounted drives and their capacities
- 🌐 **Network Statistics**: Upload/download speeds and total bandwidth
- 🔋 **Battery Information**: Battery health, charge status, and time remaining
- 🌡️ **Temperature Sensors**: CPU and system temperature monitoring
- ⚡ **Process Manager**: View top CPU and memory-consuming processes
- 📈 **Historical Graphs**: Visual representation of system metrics over time
- 🎨 **Beautiful UI**: Clean, colorful terminal interface using Rich library
- ⚙️ **Customizable**: Configure update intervals and display preferences

## Screenshots

The monitor displays:
- Real-time CPU usage with per-core breakdown
- Memory utilization with swap information
- Disk space for all volumes
- Network I/O speeds
- Battery status and health
- System temperatures
- Top resource-consuming processes

## Installation

### Prerequisites

- macOS 10.14 or later
- Python 3.8 or higher
- Homebrew (recommended)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/macbook-monitor.git
cd macbook-monitor

# Install dependencies
pip install -r requirements.txt

# Run the monitor
python monitor.py
