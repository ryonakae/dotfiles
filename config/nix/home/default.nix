{
  inputs,
  pkgs,
  ...
}:
{
  imports = [
    ./packages.nix
    ./fish.nix
    ./files.nix
    ./skills.nix
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
