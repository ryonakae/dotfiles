{
  config,
  dotfilesLink,
  inputs,
  lib,
  ...
}:
let
  skillSources =
    directory:
    if builtins.pathExists (../../. + "/${directory}") then
      lib.mapAttrs (name: _: dotfilesLink "${directory}/${name}") (
        lib.filterAttrs (name: type: type == "directory" && !(lib.hasPrefix "." name)) (
          builtins.readDir (../../. + "/${directory}")
        )
      )
    else
      { };
  shared = skillSources ".agents/skills";
  claude = shared // skillSources ".claude/skills";
  external = [
    "agent-browser"
    "agent-device"
    "cognitive-rhythm-writing"
    "cua-driver"
    "find-docs"
    "herdr"
    "japanese-tech-writing"
    "readme-creator"
    "readme-i18n"
    "skill-creator"
    "stop-slop"
    "stop-slop-ja"
    "tdd"
    "worktrunk"
  ];
  shadowed = name: builtins.hasAttr name shared || builtins.hasAttr name claude;
in
{
  programs.agent-skills = {
    enable = true;
    sources = inputs.agent-skills.lib.agent-skills.sourcesFromLock {
      manifestsDir = ../skill-sources;
      lockFile = ../skill-sources.lock.json;
    };
    skills.enable = lib.filter (name: !shadowed name) external;
    # Only local overrides need explicit per-target selection.
    skills.explicit = lib.genAttrs (lib.filter shadowed external) (
      name:
      let
        skill = config.programs.agent-skills.catalog.${name};
      in
      {
        from = skill.source;
        path = if skill.relPath == "" then "." else skill.relPath;
        agents =
          lib.optional (!(builtins.hasAttr name shared)) "agents"
          ++ lib.optional (!(builtins.hasAttr name claude)) "claude";
      }
    );
    targets = {
      agents = {
        enable = true;
        dest = ".agents/skills";
        structure = "link";
      };
      claude = {
        enable = true;
        dest = ".claude/skills";
        structure = "link";
      };
    };
  };

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
