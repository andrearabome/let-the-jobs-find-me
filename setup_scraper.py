#!/usr/bin/env python3
"""
Job Scraper Setup Script
Automatically installs dependencies and configures the scraper
"""

import os
import sys
import subprocess
import platform

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60 + "\n")

def run_command(cmd, description):
    """Run a command and show status"""
    print(f"[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[✓] {description} - Success")
            return True
        else:
            print(f"[✗] {description} - Failed")
            if result.stderr:
                print(f"    Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"[✗] {description} - Error: {str(e)[:200]}")
        return False

def check_python_version():
    """Check if Python version is 3.7+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"[✓] Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print(f"[✗] Python 3.7+ required, but {version.major}.{version.minor} found")
        return False

def check_brave_browser():
    """Check if Brave browser is installed"""
    system = platform.system()
    
    if system == "Windows":
        paths = [
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        ]
    elif system == "Darwin":  # macOS
        paths = ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
    else:  # Linux
        paths = ["/usr/bin/brave-browser", "/snap/bin/brave"]
    
    for path in paths:
        if os.path.exists(path):
            print(f"[✓] Brave browser found at: {path}")
            return True
    
    print("[!] Brave browser not found")
    print("    Download from: https://brave.com/download/")
    return False

def install_python_packages():
    """Install Python dependencies"""
    print(f"\n[*] Installing Python packages from requirements.txt...")
    
    if not os.path.exists("requirements.txt"):
        print("    [!] requirements.txt not found")
        return False
    
    cmd = f"{sys.executable} -m pip install -q -r requirements.txt"
    return run_command(cmd, "Installing base packages")

def install_optional_packages():
    """Install optional packages for browser automation"""
    packages = [
        ("selenium", "Selenium for browser automation"),
        ("webdriver-manager", "WebDriver manager for automatic driver updates"),
    ]
    
    for package, description in packages:
        cmd = f"{sys.executable} -m pip install -q {package}"
        run_command(cmd, f"Installing {description}")

def create_sample_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        print("[*] Creating .env file...")
        with open(".env", "w") as f:
            f.write("# Environment variables\n")
            f.write("FLASK_ENV=development\n")
            f.write("FLASK_DEBUG=False\n")
            f.write("SECRET_KEY=your-secret-key-here\n")
        print("[✓] .env file created")
        return True
    else:
        print("[!] .env file already exists, skipping")
        return True

def create_directories():
    """Create necessary directories"""
    directories = ["data", "logs", "cache", "backups"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[✓] Created directory: {directory}")
        else:
            print(f"[!] Directory already exists: {directory}")

def test_imports():
    """Test that all imports work"""
    print("\n[*] Testing imports...")
    
    imports = [
        ("flask", "Flask"),
        ("requests", "Requests"),
        ("bs4", "BeautifulSoup4"),
        ("lxml", "lxml"),
        ("selenium", "Selenium (optional)"),
        ("webdriver_manager", "WebDriver Manager (optional)"),
    ]
    
    for module, name in imports:
        try:
            __import__(module)
            print(f"[✓] {name} imported successfully")
        except ImportError:
            if "optional" in name:
                print(f"[!] {name} not installed (optional, required for browser automation)")
            else:
                print(f"[✗] {name} failed to import")

def test_scraper():
    """Test if scraper can be imported"""
    print("\n[*] Testing scraper module...")
    
    try:
        from browser_scraper import scrape_all_browser_jobs, get_sample_jobs_for_demo
        print("[✓] Scraper module imports successfully")
        
        # Test sample data
        jobs = get_sample_jobs_for_demo()
        print(f"[✓] Sample jobs available: {len(jobs)} jobs")
        return True
    except Exception as e:
        print(f"[✗] Scraper test failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print_header("Job Scraper Setup")
    
    print("This script will:\n")
    print("1. Check Python version")
    print("2. Check for Brave browser")
    print("3. Install Python dependencies")
    print("4. Create necessary directories")
    print("5. Test imports")
    print("6. Test scraper")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...\n")
    
    # Check Python version
    print_header("Step 1: Python Version")
    if not check_python_version():
        print("Please upgrade Python to 3.7 or later")
        sys.exit(1)
    
    # Check Brave browser
    print_header("Step 2: Brave Browser")
    brave_found = check_brave_browser()
    if not brave_found:
        print("\nWARNING: Brave browser not found!")
        print("The scraper will use API-based scraping fallback.")
        print("Install Brave for full browser automation support.\n")
    
    # Install packages
    print_header("Step 3: Install Dependencies")
    if not install_python_packages():
        print("\nFailed to install base packages")
        sys.exit(1)
    
    # Install optional packages
    install_optional_packages()
    
    # Create directories
    print_header("Step 4: Create Directories")
    create_directories()
    
    # Create .env file
    print_header("Step 5: Environment Setup")
    create_sample_env_file()
    
    # Test imports
    print_header("Step 6: Test Imports")
    test_imports()
    
    # Test scraper
    print_header("Step 7: Test Scraper")
    test_scraper()
    
    # Success message
    print_header("Setup Complete! ✓")
    print("\nNext steps:")
    print("1. Review SCRAPER_GUIDE.md for detailed documentation")
    print("2. Run: python app.py")
    print("3. Open: http://localhost:5000")
    print("4. Click 'Fetch Jobs' to start scraping")
    
    if not brave_found:
        print("\nOPTIONAL: Install Brave browser to enable advanced scraping:")
        print("  Windows: https://brave.com/download/")
        print("  macOS: brew install brave-browser")
        print("  Linux: sudo apt install brave-browser")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nSetup failed with error: {str(e)}")
        sys.exit(1)
