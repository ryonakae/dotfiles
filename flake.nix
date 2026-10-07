{
  description = "Declarative Apple Silicon macOS environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin.url = "github:nix-darwin/nix-darwin/master";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
    nix-homebrew.url = "github:zhaofengli/nix-homebrew";
    home-manager.url = "github:nix-community/home-manager/master";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    hermes-agent.url = "github:ryonakae/hermes-agent/ryonakae";
    agent-skills.url = "github:Kyure-A/agent-skills-nix";
    agent-skills.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      nix-darwin,
      home-manager,
      ...
    }:
    let
      pkgs = import inputs.nixpkgs { system = "aarch64-darwin"; };
      sourceLockProgram = inputs.agent-skills.lib.agent-skills.mkSourceLockProgram {
        inherit pkgs;
        manifestsDir = "nix/skill-sources";
        lockFile = "nix/skill-sources.lock.json";
      };
    in
    {
      formatter.aarch64-darwin = pkgs.nixfmt;
      apps.aarch64-darwin.skills-sources-lock = {
        type = "app";
        program = "${sourceLockProgram}/bin/skills-sources-lock";
      };
      darwinConfigurations.mac = nix-darwin.lib.darwinSystem {
        specialArgs = { inherit inputs; };
        modules = [
          ./nix/hosts/mac.nix
          ./nix/darwin
          inputs.nix-homebrew.darwinModules.nix-homebrew
          home-manager.darwinModules.home-manager
          (
            { config, ... }:
            {
              nixpkgs.pkgs = pkgs;
              home-manager.useGlobalPkgs = true;
              home-manager.useUserPackages = true;
              home-manager.extraSpecialArgs = { inherit inputs; };
              home-manager.sharedModules = [ inputs.agent-skills.homeManagerModules.default ];
              home-manager.users.${config.system.primaryUser} = import ./nix/home;
            }
          )
        ];
      };
    };
}
