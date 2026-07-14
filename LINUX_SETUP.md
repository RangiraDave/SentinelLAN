# SentinelLAN Linux Setup - Simple Guide

Quick setup to get device detection working on Ubuntu Linux.

## What It Does

1. **Detects connected devices** on your local network via ARP scanning
2. **Stores device info** in PostgreSQL (IP, MAC, hostname, type)
3. **Alerts on new devices** when a device connects
4. **Tracks online/offline** status of known devices

## Prerequisites

```bash
# Ubuntu 24.04 LTS
sudo apt-get update
sudo apt-get install -y \
    libpcap-dev \
    python3-dev \
    postgresql \
    postgresql-contrib
```

## Setup (10 minutes)

### 1. Install Python Dependencies

```bash
cd ~/SentinelLAN
source myvenv/bin/activate
pip install -r requirements.txt
```

### 2. Create Database

```bash
# Create PostgreSQL user and database
sudo -u postgres createuser sentinellan
sudo -u postgres createdb -O sentinellan sentinellan

# Set password
sudo -u postgres psql -c "ALTER USER sentinellan WITH PASSWORD 'sentinellan';"
```

### 3. Update Django Settings

Edit `netmonitor/settings.py`:

```python
# Find DATABASES and update to:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sentinellan',
        'USER': 'sentinellan',
        'PASSWORD': 'sentinellan',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Migrate Database

```bash
cd netmonitor
python3 manage.py migrate
python3 manage.py createsuperuser
```

### 5. Run First Scan

```bash
# Requires root privileges for ARP scanning
sudo -E python3 manage.py shell << 'EOF'
from scanner.scan_manager import run_scan
new, updated = run_scan()
print(f"New devices: {len(new)}")
print(f"Updated: {len(updated)}")
EOF
```

## Usage

### Manual Scan

```bash
sudo -E python3 manage.py shell << 'EOF'
from scanner.scan_manager import run_scan
new, updated = run_scan()
EOF
```

### View Devices

```bash
python3 manage.py shell << 'EOF'
from devices.models import Device
for dev in Device.objects.all():
    status = "Online" if dev.online else "Offline"
    print(f"{dev.ip_address} | {dev.mac_address} | {dev.hostname or 'Unknown'} | {dev.device_type} | {status}")
EOF
```

### View Alerts

```bash
python3 manage.py shell << 'EOF'
from alerts.models import Alert
for alert in Alert.objects.all().order_by('-id')[:10]:
    print(f"{alert.created_at}: {alert.message}")
EOF
```

## Periodic Scanning (Optional)

Add to crontab to scan every minute:

```bash
# Edit crontab
crontab -e

# Add this line:
* * * * * cd /home/dave/SentinelLAN/netmonitor && sudo -E python3 manage.py shell < /tmp/scan.py
```

Create `/tmp/scan.py`:

```python
from scanner.scan_manager import run_scan
try:
    new, updated = run_scan()
except Exception as e:
    print(f"Scan error: {e}")
```

## Web Dashboard

Visit http://localhost:8000/devices/ to see discovered devices.

## Troubleshooting

### "Permission denied" for ARP scanning

Use `sudo -E python3 manage.py shell`:

```bash
sudo -E python3 manage.py shell << 'EOF'
from scanner.scan_manager import run_scan
run_scan()
EOF
```

### "No active network detected"

Check your network interface:

```bash
ip addr show
python3 -c "import psutil; print(psutil.net_if_addrs())"
```

### PostgreSQL connection error

Check PostgreSQL is running:

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

---

**That's it!** Your Linux device detection system is ready.
