#!/usr/bin/env python3
"""
Installation script for Smart Money PNL Report caching requirements.
This script ensures all necessary dependencies are installed for optimal performance.
"""

import subprocess
import sys
import pkg_resources
from typing import List

def install_package(package: str) -> bool:
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        return False

def check_package_installed(package: str) -> bool:
    """Check if a package is already installed."""
    try:
        pkg_resources.get_distribution(package)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def main():
    """Main installation function."""
    print("🚀 Smart Money PNL Report - Cache Optimization Setup")
    print("=" * 50)
    
    # Required packages for caching optimization
    required_packages = [
        "cachetools==5.3.2",
        "tenacity==8.2.3"
    ]
    
    print("📦 Checking and installing required packages...")
    
    all_installed = True
    for package in required_packages:
        package_name = package.split("==")[0]
        
        if check_package_installed(package_name):
            print(f"✅ {package_name} is already installed")
        else:
            print(f"📥 Installing {package}...")
            if install_package(package):
                print(f"✅ Successfully installed {package}")
            else:
                print(f"❌ Failed to install {package}")
                all_installed = False
    
    print("\n" + "=" * 50)
    
    if all_installed:
        print("🎉 All cache optimization dependencies are ready!")
        print("\n📈 Performance improvements enabled:")
        print("   • TTL-based automatic cache expiration")
        print("   • Thread-safe concurrent access")
        print("   • Memory-efficient LRU eviction")
        print("   • Millisecond response times for cached requests")
        print("\n🕐 Cache settings:")
        print("   • Report cache: 1 hour TTL, 1000 entries max")
        print("   • Token price cache: 1 hour TTL, 10000 entries max")
        
        return True
    else:
        print("❌ Some dependencies failed to install.")
        print("Please check the errors above and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)