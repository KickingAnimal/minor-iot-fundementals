#!/bin/bash
set -e  # Quit on error

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

# ANSI color codes
GREEN="\033[1;32m"
CYAN="\033[1;36m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

info() {
    echo -e "${CYAN}[*]${RESET} $1"
}

success() {
    echo -e "${GREEN}[+]${RESET} $1"
}

error() {
    echo -e "${RED}[!]${RESET} $1"
}

ask() {
    echo -n -e "${YELLOW}[?]${RESET} $1 "
}

if grep -q "SETUP_COMPLETED = False" config.py; then
    if [ "$(id -u)" != 0 ]; then
        error "Sorry, you need to run this script with sudo!"
        exit 1
    fi

    info "Updating list of packages & installing packages to latest version."
    apt update -y && apt upgrade -y
    
    info "Enabling I2C interface"
    if grep -q "i2c-bcm2708" /etc/modules; then
        info "Seems i2c-bcm2708 module already exists, skip this step."
    else
        echo "i2c-bcm2708" >> /etc/modules
    fi
    if grep -q "dtparam=i2c1=on" /boot/config.txt; then
        info "Seems i2c1 parameter already set, skip this step."
    else
        echo "dtparam=i2c1=on" >> /boot/config.txt
    fi
    if grep -q "dtparam=i2c_arm=on" /boot/config.txt; then
        info "Seems i2c_arm parameter already set, skip this step."
    else
        echo "dtparam=i2c_arm=on" >> /boot/config.txt
    fi
    if [ -f /etc/modprobe.d/raspi-blacklist.conf ]; then
        sed -i "s/^blacklist spi-bcm2708/#blacklist spi-bcm2708/" /etc/modprobe.d/raspi-blacklist.conf
        sed -i "s/^blacklist i2c-bcm2708/#blacklist i2c-bcm2708/" /etc/modprobe.d/raspi-blacklist.conf
    else
        info "File raspi-blacklist.conf does not exist, skip this step."
    fi
    if hash i2cget 2>/dev/null; then
        info "Seems i2c-tools is installed already, skip this step."
    else
        apt-get install -y i2c-tools
    fi
    
    #Install Python requirements
    info "Installing required Python libraries."
    python3 -m pip install -r requirements.txt --break-system-packages
    
    # Set completed to True
    sed -i "s/SETUP_COMPLETED = False/SETUP_COMPLETED = True/" config.py
    
    success "Setup completed successfully!"
    info "A reboot is required for the actions to take effect."

    # Ask for reboot
    ask "Do you want to reboot now? [y/N]"
    read askReboot
    if [ $askReboot = "y" ]; then
        reboot
        exit 0
    fi
fi

info "You should see a 76 in the following table if the BME is connected correctly:"
i2cdetect -y 1
