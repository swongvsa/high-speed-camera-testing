# Camera Troubleshooting Guide

## Error -37: Network Send Error (网络数据发送错误)

**Symptom**: Camera is detected during enumeration but fails to initialize with error code -37.

**Camera Model**: HT-XGC51GC-T-C (GigE Vision camera)  
**IP Address**: 169.254.22.149 (link-local/auto-IP range)

### Diagnosis Steps

1. **Verify network adapter configuration**
   ```bash
   # Check network interfaces
   ifconfig | grep -A 5 "169.254"
   
   # Or list all interfaces
   networksetup -listallhardwareports
   ```
   
   **Expected**: Network adapter should have IP in 169.254.x.x range (same subnet as camera)

2. **Check if camera is reachable**
   ```bash
   # Ping camera
   ping -c 4 169.254.22.149
   ```
   
   **Expected**: Should receive replies. If not, network configuration is wrong.

3. **Verify firewall settings**
   ```bash
   # macOS: Check firewall status
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   
   # Temporarily disable to test (re-enable after)
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
   ```
   
   **Note**: Camera SDK needs UDP/TCP access. Firewall may block communication.

4. **Check for IP conflicts**
   ```bash
   # Scan for devices on network
   arp -a | grep "169.254"
   ```
   
   **Expected**: Camera MAC address should appear in ARP table.

5. **Verify MTU settings** (GigE cameras often require jumbo frames)
   ```bash
   # Check current MTU
   ifconfig en0 | grep mtu
   
   # Increase MTU if needed (requires sudo)
   sudo ifconfig en0 mtu 9000
   ```
   
   **Note**: Some switches don't support jumbo frames (MTU > 1500).

### Common Solutions

#### Solution 1: Set correct network adapter IP
```bash
# macOS: Set manual IP on Ethernet adapter
sudo ifconfig en0 169.254.22.100 netmask 255.255.0.0

# Verify
ifconfig en0 | grep "inet "
```

Camera and computer must be on same subnet (169.254.x.x/16).

#### Solution 2: Disable other network interfaces
```bash
# Temporarily disable WiFi (avoids routing conflicts)
networksetup -setairportpower en1 off

# Re-enable after testing
networksetup -setairportpower en1 on
```

Multiple active interfaces can cause routing issues.

#### Solution 3: Use camera manufacturer's software first
1. Install camera vendor's demo software (likely "MindVision" or similar)
2. Verify camera works with their software
3. Check what network settings they use
4. Apply same settings to your environment

#### Solution 4: Check link-local network settings

**macOS Network Preferences**:
1. Open System Preferences → Network
2. Select Ethernet adapter connected to camera
3. Configure IPv4: "Manually" or "Using DHCP with manual address"
4. Set IP: `169.254.22.100` (or any .22.x except .149)
5. Subnet Mask: `255.255.0.0`
6. Router: Leave blank
7. Click Apply

#### Solution 5: Reset camera to defaults
Consult camera manual for factory reset procedure. Camera may have incorrect IP configuration stored.

### Verification

After applying fixes, test with:

```bash
# Test 1: Ping camera
ping -c 4 169.254.22.149

# Test 2: Try camera initialization
python main.py --camera-ip 169.254.22.149 --check

# Expected output:
# Camera initialized successfully: ...
# Camera cleaned up after check
```

### Still Not Working?

If error persists after trying all solutions:

1. **Check camera hardware**
   - Is LED blinking/solid? (indicates power/link status)
   - Try different Ethernet cable
   - Try different network adapter/port

2. **Verify SDK installation**
   ```bash
   # Check SDK library exists
   ls -la spec/macsdk*/lib/*.dylib
   
   # Verify Python can load SDK
   python -c "from src.lib import mvsdk; print(mvsdk.__file__)"
   ```

3. **Check for driver conflicts**
   ```bash
   # Look for multiple camera drivers
   kextstat | grep -i camera
   ```

4. **Contact camera vendor support**
   - Provide error code: -37
   - Provide SDK version: 2.1.0.6
   - Provide camera model: HT-XGC51GC-T-C
   - Provide OS: macOS (Darwin 24.5.0)

## Quick Diagnostic Command

Run this to check network configuration:

```bash
echo "=== Network Configuration ===" && \
ifconfig | grep -A 5 "169.254" && \
echo -e "\n=== Camera Ping Test ===" && \
ping -c 2 169.254.22.149 && \
echo -e "\n=== ARP Table ===" && \
arp -a | grep "169.254" && \
echo -e "\n=== Firewall Status ===" && \
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

## Expected Working Configuration

**Network Adapter** (Ethernet connected to camera):
- IP Address: 169.254.22.100 (or any .22.x except .149)
- Subnet Mask: 255.255.0.0
- Router: None
- MTU: 1500 or 9000 (if switch supports jumbo frames)

**Camera**:
- IP Address: 169.254.22.149
- Reachable via ping
- Visible in ARP table
- No firewall blocking

**Software**:
- MVSDK installed in spec/macsdk*/
- Python environment has dependencies
- No other camera software running

---

For more help, see:
- Camera manual (spec/manual.txt)
- MVSDK documentation (spec/macsdk*/docs/)
- Online support forums
