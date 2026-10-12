{ pkgs, ... }:
{
  imports = [
    ./homebrew.nix
    ./preferences.nix
  ];

  nixpkgs.hostPlatform = "aarch64-darwin";
  system.stateVersion = 6;

  programs.fish.enable = true;
  environment.shells = [ pkgs.fish ];

  nix.enable = true;
  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

}
