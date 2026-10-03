{ machine, ... }:
{
  imports = [ ./homebrew.nix ];

  nixpkgs.hostPlatform = "aarch64-darwin";
  system.stateVersion = 6;
  system.primaryUser = machine.username;
  users.users.${machine.username}.home = machine.homeDirectory;

  nix.enable = true;
  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

  assertions = [
    {
      assertion = machine.username != "" && machine.homeDirectory != "";
      message = "Supply a non-secret host.json using scripts/dotfiles.sh --host DIRECTORY.";
    }
  ];
}
