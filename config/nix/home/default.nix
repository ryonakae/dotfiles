{ machine, ... }:
{
  imports = [
    ./packages.nix
    ./fish.nix
    ./files.nix
    ./protection.nix
  ];

  home.username = machine.username;
  home.homeDirectory = machine.homeDirectory;
  home.stateVersion = "26.05";
}
