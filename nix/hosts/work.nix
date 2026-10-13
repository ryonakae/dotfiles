{ lib, ... }:
{
  system.activationScripts.power.text = lib.mkAfter ''
    /usr/bin/pmset -a lowpowermode 0
    /usr/bin/pmset -b lessbright 1 displaysleep 2 disksleep 0 womp 0
    /usr/bin/pmset -c sleep 0 displaysleep 20 disksleep 10 womp 1
  '';
}
