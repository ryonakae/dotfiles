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
    skills-agent-browser = {
      url = "github:vercel-labs/agent-browser";
      flake = false;
    };
    skills-agent-device = {
      url = "github:callstack/agent-device";
      flake = false;
    };
    skills-tech-writing = {
      url = "github:f4ah6o/tech-write-ja";
      flake = false;
    };
    skills-cua-driver = {
      url = "github:trycua/cua";
      flake = false;
    };
    skills-find-docs = {
      url = "github:upstash/context7";
      flake = false;
    };
    skills-herdr = {
      url = "github:herdrdev/herdr";
      flake = false;
    };
    skills-readme-creator = {
      url = "github:mblode/agent-skills";
      flake = false;
    };
    skills-readme-i18n = {
      url = "github:xixu-me/skills";
      flake = false;
    };
    skills-skill-creator = {
      url = "github:anthropics/skills";
      flake = false;
    };
    skills-stop-slop = {
      url = "github:hardikpandya/stop-slop";
      flake = false;
    };
    skills-stop-slop-ja = {
      url = "github:kyaukyuai/stop-slop-ja";
      flake = false;
    };
    skills-tdd = {
      url = "github:mattpocock/skills";
      flake = false;
    };
    skills-worktrunk = {
      url = "github:max-sixty/worktrunk";
      flake = false;
    };
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
    in
    {
      formatter.aarch64-darwin = pkgs.nixfmt;
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
