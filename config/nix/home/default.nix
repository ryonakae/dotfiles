{
  config,
  inputs,
  pkgs,
  ...
}:
let
  dotfilesConfig = "${config.home.homeDirectory}/dotfiles/config";
in
{
  _module.args.dotfilesConfig = dotfilesConfig;
  # Live links inherit checkout permissions; an executable override can force a build-time copy.
  _module.args.dotfilesLink =
    relativePath: config.lib.file.mkOutOfStoreSymlink "${dotfilesConfig}/${relativePath}";

  imports = [
    ./packages.nix
    ./fish.nix
    ./files.nix
    ./pi.nix
    ./skills.nix
    ./protection.nix
    ./hermes.nix
  ];

  # Local voice pulls in PyTorch through CTranslate2's build-time checks.
  _module.args.hermes =
    inputs.hermes-agent.packages.${pkgs.stdenv.hostPlatform.system}.default.override
      (args: {
        extraDependencyGroups = builtins.filter (group: group != "voice") args.extraDependencyGroups;
      });

  home.stateVersion = "26.05";
}
