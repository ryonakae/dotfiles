{
  description = "Declarative Apple Silicon macOS environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin.url = "github:nix-darwin/nix-darwin/master";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
    home-manager.url = "github:nix-community/home-manager/master";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
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
      hostFile =
        if builtins.pathExists "${host}/host.json" then
          "${host}/host.json"
        else
          "${host}/host.json.example";
      machine = builtins.fromJSON (builtins.readFile hostFile);
    in
    {
      formatter.aarch64-darwin = inputs.nixpkgs.legacyPackages.aarch64-darwin.nixfmt;
      darwinConfigurations.mac = nix-darwin.lib.darwinSystem {
        specialArgs = { inherit inputs machine; };
        modules = [
          ./config/nix/darwin
          home-manager.darwinModules.home-manager
          {
            home-manager.useGlobalPkgs = true;
            home-manager.useUserPackages = true;
            home-manager.extraSpecialArgs = { inherit inputs machine; };
            home-manager.users.${machine.username} = import ./config/nix/home;
          }
        ];
      };
    };
}
