#!/bin/bash
set -euo pipefail

if [[ $# == 2 && $2 == --yes ]]; then
  preapproved=1
elif [[ $# == 1 ]]; then
  preapproved=0
else
  echo 'Usage: macos-settings.sh default|private|work [--yes]' >&2
  exit 2
fi
case $1 in
  default) exit 0 ;;
  private|work) ;;
  *) echo "Unknown configuration: $1" >&2; exit 2 ;;
esac

if [[ ${APP_SANDBOX_CONTAINER_ID:-} == agent-safehouse || $EUID == 0 ]]; then
  echo 'Run as the target user outside Safehouse, not as root.' >&2
  exit 1
fi

if [[ $preapproved == 0 ]]; then
  printf 'Apply %s power settings to this Mac?\n' "$1"
  read -r -p "Type 'apply' to continue: " answer
  [[ $answer == apply ]] || exit 1
fi
case $1 in
  private)
    support=$(sudo -n /usr/sbin/systemsetup -getRestartPowerFailure)
    if [[ $support == *"Not supported"* ]]; then
      echo 'Restart after power failure is not supported on this Mac.' >&2
      exit 1
    fi
    sudo -n /usr/sbin/systemsetup -setRestartPowerFailure on
    sudo -n /usr/sbin/systemsetup -setComputerSleep never
    sudo -n /usr/sbin/systemsetup -setDisplaySleep 20
    sudo -n /usr/sbin/systemsetup -setHardDiskSleep never
    sudo -n /usr/sbin/systemsetup -setAllowPowerButtonToSleepComputer off
    ;;
  work)
    sudo -n /usr/bin/pmset -a lowpowermode 0
    sudo -n /usr/bin/pmset -b lessbright 1 displaysleep 2 disksleep 0 womp 0
    sudo -n /usr/bin/pmset -c sleep 0 displaysleep 20 disksleep 10 womp 1
    ;;
esac
