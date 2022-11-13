#!/bin/bash


# run this script:
#curl https://raw.githubusercontent.com/michimussato/JukeOroni/develop/install.sh | bash
printf "hello"


# # # System
# https://raspberrypi.stackexchange.com/questions/28907/how-could-one-automate-the-raspbian-raspi-config-setup

# Set password
#(echo \"raspberry\" ; echo \"pi\" ; echo \"pi\") | passwd

# connect to wifi

# set wifi country
#sudo raspi-config nonint do_wifi_country "CH"

# set hostname
#sudo raspi-config nonint do_hostname "jukeoroni.local"

# enable ssh
#sudo raspi-config nonint do_ssh 0

# disable onboard audio
#if grep -q "^dtparam=audio=on" /boot/config.txt; then
#    sudo sed -i "/^dtparam=audio=on$/ s|^|#|" sudo nano /boot/config.txt

# enable i2c
#sudo raspi-config nonint do_i2c 0

# enable spi
#sudo raspi-config nonint do_spi 0

# # set locale
# # en_US.UTF-8
#sudo nano /etc/default/locale
#LANG=en_US.UTF-8
#LC_ALL=en_US.UTF-8
#LANGUAGE=en_US.UTF-8

# # update system
#sudo apt-get update
#sudo apt-get upgrade
#sudo apt-get autoremove


# # # Git
#sudo apt-get install git
#git clone https://github.com/michimussato/jukeoroni.git /data/django/jukeoroni/
#cd /data/django/jukeoroni
#git checkout develop


# # # Git Crypt
# # create key file: https://buddy.works/guides/git-crypt
#sudo apt-get install git-crypt
#cp /data/googledrive/temp/git-crypt-key /data/django/
#cd /data/django/jukeoroni
#git-crypt unlock /data/django/git-crypt-key


# # # Google Drive
#sudo apt-get install rclone
#sudo mkdir -p /data/googledrive
#sudo chown -R pi:pi /data/

# automate:
#rclone config

# Service
#sudo nano /etc/systemd/system/googledrive.service
#[Unit]
#Description=rclone GDrive Service
#After=network.target
#StartLimitIntervalSec=0
#
#[Service]
#Type=simple
#Restart=always
#RestartSec=1
#User=pi
#ExecStart=nice -5 rclone mount googledrive: /data/googledrive --vfs-cache-mode writes
#
#[Install]
#WantedBy=multi-user.target

# Enable service
#sudo systemctl enable googledrive


# # # Player

# Service
#sudo nano /etc/systemd/system/jukeoroni.service
#[Unit]
#Description=JukeOroni Service
#After=googledrive.serivce
#StartLimitIntervalSec=0
#
#[Service]
#Type=simple
#Restart=always
#RestartSec=1
#User=pi
#ExecStartPre=/bin/sleep 15
#ExecStart=/data/venv/bin/python /data/JukeOroniy/player.py
#
#[Install]
#WantedBy=multi-user.target

# Enable service
#sudo systemctl enable jukeoroni


# # # Transmission

#sudo apt install transmission-daemon
#sudo systemctl status transmission-daemon
#sudo systemctl stop transmission-daemon

# # edit while service is off
#sudo nano /etc/systemd/system/multi-user.target.wants/transmission-daemon.service
# add googledrive.service dependency and change user
#[Unit]
#Description=Transmission BitTorrent Daemon
#After=network.target googledrive.service
#
#[Service]
#User=pi
#Type=notify
#ExecStartPre=/bin/sleep 15
#ExecStart=nice -10 /usr/bin/transmission-daemon -f --log-error
#ExecStop=/bin/kill -s STOP $MAINPID
#ExecReload=/bin/kill -s HUP $MAINPID
#
#[Install]
#WantedBy=multi-user.target

#sudo mkdir -p /data/transmission/in_progress
#sudo chown -R pi:pi /data/transmission/in_progress

#sudo nano /etc/transmission-daemon/settings.json
#{
#    "alt-speed-down": 512,
#    "alt-speed-enabled": false,
#    "alt-speed-time-begin": 540,
#    "alt-speed-time-day": 127,
#    "alt-speed-time-enabled": false,
#    "alt-speed-time-end": 1020,
#    "alt-speed-up": 0,
#    "bind-address-ipv4": "0.0.0.0",
#    "bind-address-ipv6": "::",
#    "blocklist-enabled": false,
#    "blocklist-url": "http://www.example.com/blocklist",
#    "cache-size-mb": 4,
#    "dht-enabled": true,
#    "download-dir": "/data/googledrive/media/torrents",
#    "download-limit": 100,
#    "download-limit-enabled": 0,
#    "download-queue-enabled": true,
#    "download-queue-size": 5,
#    "encryption": 1,
#    "idle-seeding-limit": 30,
#    "idle-seeding-limit-enabled": false,
#    "incomplete-dir": "/data/transmission/in_progress",
#    "incomplete-dir-enabled": true,
#    "lpd-enabled": false,
#    "max-peers-global": 200,
#    "message-level": 1,
#    "peer-congestion-algorithm": "",
#    "peer-id-ttl-hours": 6,
#    "peer-limit-global": 200,
#    "peer-limit-per-torrent": 50,
#    "peer-port": 51413,
#    "peer-port-random-high": 65535,
#    "peer-port-random-low": 49152,
#    "peer-port-random-on-start": false,
#    "peer-socket-tos": "default",
#    "pex-enabled": true,
#    "port-forwarding-enabled": false,
#    "preallocation": 1,
#    "prefetch-enabled": true,
#    "queue-stalled-enabled": true,
#    "queue-stalled-minutes": 30,
#    "ratio-limit": 2,
#    "ratio-limit-enabled": false,
#    "rename-partial-files": true,
#    "rpc-authentication-required": true,
#    "rpc-bind-address": "0.0.0.0",
#    "rpc-enabled": true,
#    "rpc-host-whitelist": "",
#    "rpc-host-whitelist-enabled": true,
#    "rpc-password": "transmission",
#    "rpc-port": 9091,
#    "rpc-url": "/transmission/",
#    "rpc-username": "transmission",
#    "rpc-whitelist": "127.0.0.1",
#    "rpc-whitelist-enabled": false,
#    "scrape-paused-torrents-enabled": true,
#    "script-torrent-done-enabled": false,
#    "script-torrent-done-filename": "/data/transmission/script_torrent_done.sh",
#    "seed-queue-enabled": false,
#    "seed-queue-size": 10,
#    "speed-limit-down": 512,
#    "speed-limit-down-enabled": false,
#    "speed-limit-up": 0,
#    "speed-limit-up-enabled": true,
#    "start-added-torrents": true,
#    "trash-original-torrent-files": false,
#    "umask": 18,
#    "upload-limit": 0,
#    "upload-limit-enabled": 1,
#    "upload-slots-per-torrent": 14,
#    "utp-enabled": true
#}

#sudo nano /etc/init.d/transmission-daemon
# USER=debian-transmission => USER=pi

#sudo chown -R pi:pi /etc/transmission-daemon
#sudo mkdir -p /home/pi/.config/transmission-daemon/
#sudo ln -s /etc/transmission-daemon/settings.json /home/pi/.config/transmission-daemon/
#sudo chown -R pi:pi /home/pi/.config/transmission-daemon/

#sudo systemctl enable transmission-daemon


# # omxplayer
# sudo apt-get install omxplayer
# https://python-omxplayer-wrapper.readthedocs.io/en/latest/
# sudo apt-get update && sudo apt-get install -y libdbus-1{,-dev}
# sudo apt-get update && sudo apt-get install -y libdbus-1-3
# sudo apt-get update && sudo apt-get install -y libdbus-1-dev
# pip install omxplayer-wrapper

# sudo apt-get install imagemagick


alsa
pip install pyalsaaudio
