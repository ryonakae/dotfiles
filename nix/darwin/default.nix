{ ... }:
{
  imports = [
    ./homebrew.nix
    ./preferences.nix
  ];

  nixpkgs.hostPlatform = "aarch64-darwin";
  system.stateVersion = 6;

  programs.fish.enable = true;

  nix.enable = true;
  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

}
