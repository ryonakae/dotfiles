{ home-manager, pkgs }:
let
  host = import ./hosts/default.nix;
  username = host.system.primaryUser;
in
(home-manager.lib.homeManagerConfiguration {
  inherit pkgs;
  modules = [
    ({ lib, ... }: {
      home = {
        inherit username;
        homeDirectory = host.users.users.${username}.home;
        stateVersion = "26.05";
        file = pkgs.lib.mkForce { };
      };
      # Disabling launchd alone still removes agents from the old generation.
      home.activation.setupLaunchAgents = lib.mkForce (lib.hm.dag.entryAnywhere "");
      launchd.enable = false;
      targets.darwin.copyApps.enable = false;
      targets.darwin.linkApps.enable = false;
      # Match the embedded activation without reinstalling user packages.
      submoduleSupport = {
        enable = true;
        externalPackageInstall = true;
      };
    })
  ];
}).activationPackage
