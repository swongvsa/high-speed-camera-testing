#!/usr/bin/env python3
"""
Quick fix script to change camera IP address to resolve conflict.
This changes the camera's IP instead of your computer's IP.
"""

import sys
from src.lib import mvsdk


def main():
    try:
        # Get raw camera device info from SDK
        dev_list = mvsdk.CameraEnumerateDevice()
        if not dev_list:
            print("No cameras found!")
            return 1

        # Use first camera (index 0)
        dev_info = dev_list[0]
        print(f"Found camera: {dev_info.GetFriendlyName()}")
        print(f"Port Type: {dev_info.GetPortType()}")
        print(f"Serial Number: {dev_info.GetSn()}")

        # Check if camera is already opened
        if mvsdk.CameraIsOpened(dev_info):
            print("⚠️  Camera is currently opened. Closing it first...")
            # Cannot close without handle, so this will fail if another process has it open
            print("❌ Please close any other programs using the camera and try again.")
            return 1

        # Get current IP configuration
        try:
            cam_ip, cam_mask, cam_gw, eth_ip, eth_mask, eth_gw = mvsdk.CameraGigeGetIp(dev_info)
            print(f"\nCurrent camera IP: {cam_ip}")
            print(f"Current subnet mask: {cam_mask}")
            print(f"Current gateway: {cam_gw}")
            print(f"\nAdapter IP: {eth_ip}")
            print(f"Adapter subnet: {eth_mask}")
        except Exception as e:
            print(f"Warning: Could not get current IP info: {e}")

        # Change camera IP to 169.254.170.200
        new_ip = "169.254.170.200"
        subnet = "255.255.0.0"
        gateway = "0.0.0.0"  # Use 0.0.0.0 for link-local instead of empty string

        print(f"\n🔧 Changing camera IP to: {new_ip}")
        print(f"   Subnet: {subnet}")
        print(f"   Gateway: {gateway}")
        print(f"   Persistent: True")

        result = mvsdk.CameraGigeSetIp(
            dev_info,
            new_ip,
            subnet,
            gateway,
            True,  # Persistent
        )

        if result == 0:
            print(f"\n✅ Success! Camera IP changed to {new_ip}")
            print(f"\nNext steps:")
            print(f"  1. Wait 5 seconds for camera to reboot")
            print(f"  2. Run: python main.py --camera-ip {new_ip} --check")
            return 0
        else:
            error_msg = {
                -1: "CAMERA_STATUS_FAILED - General failure",
                -4: "CAMERA_STATUS_NOT_SUPPORTED - Function not supported",
                -6: "CAMERA_STATUS_PARAMETER_INVALID - Invalid parameters",
                -12: "CAMERA_STATUS_TIME_OUT - Timeout",
                -14: "CAMERA_STATUS_COMM_ERROR - Communication error",
            }.get(result, f"Unknown error code: {result}")

            print(f"\n❌ Failed to change camera IP")
            print(f"   Error: {error_msg}")
            print(f"\nTroubleshooting:")
            print(f"  • Try running with sudo: sudo $(which python) fix_camera_ip.py")
            print(f"  • Ensure no other program is using the camera")
            print(f"  • Check if camera supports dynamic IP configuration")
            print(f"  • Try power-cycling the camera")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
