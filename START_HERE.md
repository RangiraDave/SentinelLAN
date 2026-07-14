# Next Steps - Start Here!

## What You Have Now

Your SentinelLAN project is **ready to run on Ubuntu Linux**. 

✅ Detects new devices on network  
✅ Stores in PostgreSQL  
✅ Generates alerts  
✅ Works on Linux (no Npcap needed)  

## Step 1: Install System Packages (2 minutes)

```bash
sudo apt-get update
sudo apt-get install -y libpcap-dev python3-dev postgresql postgresql-contrib
```

## Step 2: Install Python Dependencies (2 minutes)

```bash
cd ~/SentinelLAN
source myvenv/bin/activate
pip install -r requirements.txt
```

## Step 3: Set Up PostgreSQL (5 minutes)

```bash
# Create database and user
sudo -u postgres createuser sentinellan
sudo -u postgres createdb -O sentinellan sentinellan

# Set password
sudo -u postgres psql -c "ALTER USER sentinellan WITH PASSWORD 'sentinellan';"
```

## Step 4: Configure Django (5 minutes)

Edit `netmonitor/settings.py`:

Find this section:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Replace with:
```python
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

## Step 5: Create Database Tables (2 minutes)

```bash
cd ~/SentinelLAN/netmonitor
python3 manage.py migrate
python3 manage.py createsuperuser
```

## Step 6: Run Your First Scan (2 minutes)

```bash
sudo -E python3 manage.py shell << 'EOF'
from scanner.scan_manager import run_scan
new_devices, updated_devices = run_scan()
print(f"✓ New devices: {len(new_devices)}")
print(f"✓ Updated: {len(updated_devices)}")
EOF
```

## Step 7: View Results

**View all devices:**
```bash
python3 manage.py shell << 'EOF'
from devices.models import Device
print("All Devices:")
for device in Device.objects.all():
    status = "🟢 Online" if device.online else "🔴 Offline"
    print(f"  {device.ip_address} | {device.mac_address} | {device.hostname or 'Unknown'} | {device.device_type} | {status}")
EOF
```

**View alerts:**
```bash
python3 manage.py shell << 'EOF'
from alerts.models import Alert
print("Recent Alerts:")
for alert in Alert.objects.all().order_by('-id')[:10]:
    print(f"  {alert.created_at}: {alert.message}")
EOF
```

**View in browser:**
```bash
cd netmonitor
python3 manage.py runserver
# Visit http://localhost:8000/devices/
```

## Step 8 (Optional): Set Up Automatic Scanning

Scan every minute automatically:

```bash
# Create scan script
cat > /tmp/network_scan.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netmonitor.settings')
django.setup()

from scanner.scan_manager import run_scan
try:
    new, updated = run_scan()
    print(f"Scan complete: {len(new)} new, {len(updated)} updated")
except Exception as e:
    print(f"Scan error: {e}")
    sys.exit(1)
EOF

# Add to crontab
(crontab -l 2>/dev/null; echo "* * * * * cd /home/dave/SentinelLAN/netmonitor && sudo -E python3 /tmp/network_scan.py") | crontab -
```

## What's Happening

```
Your network        →  ARP Scan   →  Process   →  PostgreSQL   →  Alerts
(192.168.1.0/24)      (find IPs)     (add type)    (store data)    (new device!)
```

## What Gets Stored for Each Device

- **IP Address** - 192.168.1.100
- **MAC Address** - aa:bb:cc:dd:ee:ff
- **Hostname** - "user-laptop" (from reverse DNS)
- **Vendor** - "Apple Inc." (from MAC lookup)
- **Type** - computer/phone/printer/smart_home/etc.
- **Online Status** - True/False
- **First Seen** - When first detected
- **Last Seen** - Last scan time

## Troubleshooting

### "Permission denied" for ARP scanning

ARP scanning needs root. Always use `sudo -E`:

```bash
sudo -E python3 manage.py shell << 'EOF'
...
EOF
```

### "No active network detected"

Check your network:

```bash
ip addr show
# OR
python3 -c "import psutil; print([(n, [a.address for a in addrs]) for n, addrs in psutil.net_if_addrs().items()])"
```

### PostgreSQL errors

Make sure PostgreSQL is running:

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql  # if not running
```

### Django database errors

If migrations fail:

```bash
cd netmonitor
python3 manage.py showmigrations
python3 manage.py migrate --verbosity 2
```

## Key Files

- `scanner/discovery.py` - Device detection logic
- `scanner/arp_scanner.py` - ARP scanning
- `scanner/network_info.py` - Network detection
- `scanner/scan_manager.py` - Coordinates the scan
- `devices/models.py` - Device database model
- `alerts/models.py` - Alert database model

## That's It!

You now have a working device detection system on Linux:

✅ Scans local network automatically  
✅ Stores device info in PostgreSQL  
✅ Alerts when new device connects  
✅ Shows online/offline status  

---

**Question?** Check [LINUX_SETUP.md](LINUX_SETUP.md) for more details.

**Need help?** All original code is here - just scan with `sudo -E`!
