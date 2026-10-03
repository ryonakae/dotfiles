{
  config,
  lib,
  pkgs,
  ...
}:
let
  skillSources =
    directory:
    if builtins.pathExists directory then
      lib.mapAttrs (name: _: directory + "/${name}") (
        lib.filterAttrs (name: type: type == "directory" && !(lib.hasPrefix "." name)) (
          builtins.readDir directory
        )
      )
    else
      { };
  shared = (import ./external-skills.nix { inherit pkgs; }) // skillSources ../../.agents/skills;
  claude = shared // skillSources (../../.claude + "/skills");
in
{
  home.file =
    lib.mapAttrs' (name: source: lib.nameValuePair ".agents/skills/${name}" { inherit source; }) shared
    // lib.mapAttrs' (
      name: source: lib.nameValuePair ".claude/skills/${name}" { inherit source; }
    ) claude
    // {
      # Share the live skill collection, not live sources from this repository.
      ".gemini/antigravity-cli/skills".source =
        config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/.agents/skills";
    };
}
