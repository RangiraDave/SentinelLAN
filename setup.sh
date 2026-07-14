#!/bin/bash
# SentinelLAN Setup Script - Copy and paste into terminal

echo "🚀 SentinelLAN Setup for Ubuntu Linux"
echo "===================================="

# Step 1: Install system packages
echo -e "\n1️⃣ Installing system packages..."
sudo apt-get update
sudo apt-get install -y libpcap-dev python3-dev postgresql postgresql-contrib

# Step 2: Install Python dependencies
echo -e "\n2️⃣ Installing Python dependencies..."
cd ~/SentinelLAN
source myvenv/bin/activate
pip install -r requirements.txt

# Step 3: PostgreSQL setup
echo -e "\n3️⃣ Setting up PostgreSQL..."
sudo -u postgres createuser sentinellan 2>/dev/null || echo "User already exists"
sudo -u postgres createdb -O sentinellan sentinellan 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "ALTER USER sentinellan WITH PASSWORD 'sentinellan';"

# Step 4: Django settings (you need to edit this manually)
echo -e "\n4️⃣ ⚠️  MANUAL STEP: Edit netmonitor/settings.py"
echo "   Replace the DATABASES section with PostgreSQL config"
echo "   See START_HERE.md for details"
read -p "Press Enter when done..."

# Step 5: Run migrations
echo -e "\n5️⃣ Running database migrations..."
cd netmonitor
python3 manage.py migrate

# Step 6: Create admin user
echo -e "\n6️⃣ Creating admin user..."
python3 manage.py createsuperuser

# Step 7: Test scan
echo -e "\n7️⃣ Testing network scan..."
sudo -E python3 manage.py shell << 'EOFPYTHON'
from scanner.scan_manager import run_scan
try:
    new, updated = run_scan()
    print(f"✅ Scan successful!")
    print(f"   New devices: {len(new)}")
    print(f"   Updated: {len(updated)}")
except Exception as e:
    print(f"❌ Scan failed: {e}")
EOFPYTHON

echo -e "\n✅ Setup complete!"
echo "Next: python3 manage.py runserver"
echo "      Visit http://localhost:8000/devices/"
