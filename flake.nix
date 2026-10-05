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
    host = {
      url = "path:./config/nix/hosts";
      flake = false;
    };
  };

  outputs =
    inputs@{
      nix-darwin,
      home-manager,
      host,
      ...
    }:
    let
      pkgs = import inputs.nixpkgs {
        system = "aarch64-darwin";
        config.allowUnfreePredicate =
          pkg:
          builtins.elem (inputs.nixpkgs.lib.getName pkg) [
            "claude-code"
            "antigravity-cli"
          ];
      };
      hostFile =
        if builtins.pathExists "${host}/host.json" then
          "${host}/host.json"
        else
          "${host}/host.json.example";
      machine = builtins.fromJSON (builtins.readFile hostFile);
      sourceLockProgram = inputs.agent-skills.lib.agent-skills.mkSourceLockProgram {
        inherit pkgs;
        manifestsDir = "config/nix/skill-sources";
        lockFile = "config/nix/skill-sources.lock.json";
      };
    in
    {
      formatter.aarch64-darwin = pkgs.nixfmt;
      apps.aarch64-darwin.skills-sources-lock = {
        type = "app";
        program = "${sourceLockProgram}/bin/skills-sources-lock";
      };
      darwinConfigurations.mac = nix-darwin.lib.darwinSystem {
        specialArgs = { inherit inputs machine; };
        modules = [
          ./config/nix/darwin
          inputs.nix-homebrew.darwinModules.nix-homebrew
          home-manager.darwinModules.home-manager
          {
            nixpkgs.pkgs = pkgs;
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.extraSpecialArgs = { inherit inputs machine; };
            home-manager.sharedModules = [ inputs.agent-skills.homeManagerModules.default ];
            home-manager.users.${machine.username} = import ./config/nix/home;
          }
        ];
      };
    };
}
