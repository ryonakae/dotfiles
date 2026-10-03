{ machine, ... }:
{
  imports = [ ./packages.nix ];

  home.username = machine.username;
  home.homeDirectory = machine.homeDirectory;
  home.stateVersion = "26.05";
}
