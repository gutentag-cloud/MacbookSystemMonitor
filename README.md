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
git clone https://github.com/gutentag-cloud/MacbookSystemMonitor.git
cd MacbookSystemMonitor

# Install dependencies
pip3 install -r requirements.txt

# Run the monitor
python3 monitor.py
```

### Optional: Install system monitoring tools

```bash

#### Temperature & Sensor Monitoring (Highly Recommended)

For comprehensive sensor monitoring including CPU/GPU temperature, fan speeds, and power consumption:

```bash
# Install osx-cpu-temp (lightweight, CPU temperature only)
brew install osx-cpu-temp

# Verify it works
osx-cpu-temp
# Should output: XX.X°C

# Install iStats (comprehensive - CPU, GPU, battery temp, fans, etc.)
sudo gem install iStats

# Verify it works
istats
# Should show detailed sensor information
```

## Usage

### Basic Usage

```bash
python monitor.py
```

### Command Line Options

```bash
# Update every 2 seconds
python monitor.py --interval 2

# Minimal view (less details)
python monitor.py --minimal

# Show only specific monitors
python monitor.py --only cpu,memory,battery

# Export data to JSON
python monitor.py --export data.json

# Show help
python monitor.py --help
```

## Keyboard Shortcuts

* **`q`** or **`Ctrl+C`**: Quit the monitor
* **`p`**: Pause/Resume updates
* **`r`**: Reset statistics
* **`s`**: Save current snapshot
* **`h`**: Toggle help menu
* **`1-7`**: Toggle individual monitor panels

## Configuration

Edit `config/settings.json` to customize:

```json
{
  "update_interval": 1.0,
  "history_length": 60,
  "temperature_unit": "celsius",
  "network_unit": "MB",
  "show_graphs": true,
  "color_theme": "default"
}
```

## Features in Detail

### CPU Monitor
* Overall CPU usage percentage
* Per-core usage breakdown
* CPU frequency monitoring
* Load average (1, 5, 15 minutes)
* Historical usage graph

### Memory Monitor
* Total, used, and available RAM
* Swap memory usage
* Memory pressure indicator
* Per-app memory consumption
* Cache and buffer statistics

### Disk Monitor
* Usage for all mounted volumes
* Read/write speeds
* SMART status (if available)
* Disk health indicators

### Network Monitor
* Real-time upload/download speeds
* Total bandwidth consumed
* Active connections count
* Network interface status

### Battery Monitor
* Current charge percentage
* Time remaining estimate
* Power source (battery/AC)
* Battery health and cycle count
* Charging/discharging rate

### Temperature Monitor
* CPU temperature
* GPU temperature (if available)
* Battery temperature
* Thermal pressure indicators

### Process Monitor
* Top CPU-consuming processes
* Top memory-consuming processes
* Process count
* Thread count

## Troubleshooting

### Permission Issues
Some features require elevated permissions:

```bash
sudo python monitor.py
```

### Temperature Not Showing
Install temperature monitoring tools:

```bash
brew install osx-cpu-temp
```

### High CPU Usage
Increase the update interval:

```bash
python monitor.py --interval 2
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

* [psutil](https://github.com/giampaolo/psutil) - Cross-platform system monitoring
* [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
* [osx-cpu-temp](https://github.com/lavoiesl/osx-cpu-temp) - Temperature monitoring

## Support

If you found this helpful, please give it a ⭐️!
For issues and questions, please use the GitHub Issues page.
