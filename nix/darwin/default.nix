{ config, pkgs, dotfilesBuild, ... }:
let
  home = config.home-manager.users.${config.system.primaryUser};
in
{
  imports = [
    ./homebrew.nix
    ./preferences.nix
  ];

  nixpkgs.hostPlatform = "aarch64-darwin";
  system.stateVersion = 6;

  environment.etc."dotfiles/build.json".text = builtins.toJSON (dotfilesBuild // {
    username = home.home.username;
    homeDirectory = home.home.homeDirectory;
    hermesCheck = toString home.xdg.configFile."hermes/check-stopped.sh".source;
    mise = "${home.programs.mise.package}/bin/mise";
  });

  programs.fish.enable = true;
  environment.shells = [ pkgs.fish ];

  nix.enable = true;
  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

}
