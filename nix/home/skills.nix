{
  config,
  inputs,
  lib,
  ...
}:
let
  dotfiles = (builtins.fromTOML (builtins.readFile ../../mise.default.toml)).dotfiles;
  localSkills =
    agent:
    let
      prefix = "~/.${agent}/skills/";
      pattern = "${prefix}[!.]*";
      directory = ../../. + "/${builtins.dirOf dotfiles.${pattern}.source}";
      common = lib.filterAttrs (name: type: type == "directory" && !(lib.hasPrefix "." name)) (
        builtins.readDir directory
      );
      overrides = lib.mapAttrs' (target: _: lib.nameValuePair (lib.removePrefix prefix target) true) (
        lib.filterAttrs (target: _: lib.hasPrefix prefix target && target != pattern) dotfiles
      );
    in
    common // overrides;
  shared = localSkills "agents";
  claude = localSkills "claude";
  external = [
    "agent-browser"
    "agent-device"
    "cognitive-rhythm-writing"
    "find-docs"
    "ghostwriter"
    "herdr"
    "japanese-tech-writing"
    "ketch"
    "readme-i18n"
    "skill-creator"
    "stop-slop"
    "stop-slop-ja"
    "tdd"
    "worktrunk"
  ];
  shadowed = name: builtins.hasAttr name shared || builtins.hasAttr name claude;
  cuaSkills = {
    cua-driver = "cua-driver/rust/Skills/cua-driver";
    cua-spaces = "cua/skills/cua-spaces";
  };
  targetsFor =
    name:
    lib.optional (!(builtins.hasAttr name shared)) "agents"
    ++ lib.optional (!(builtins.hasAttr name claude)) "claude";
in
{
  programs.agent-skills = {
    enable = true;
    sources = inputs.agent-skills.lib.agent-skills.sourcesFromLock {
      manifestsDir = ../skill-sources;
      lockFile = ../skill-sources.lock.json;
    };
    skills.enable = lib.filter (name: !shadowed name) external;
    skills.explicit =
      lib.mapAttrs (name: path: {
        from = "cua-driver";
        inherit path;
        agents = targetsFor name;
      }) cuaSkills
      // lib.genAttrs (lib.filter shadowed external) (
        name:
        let
          skill = config.programs.agent-skills.catalog.${name};
        in
        {
          from = skill.source;
          path = if skill.relPath == "" then "." else skill.relPath;
          agents = targetsFor name;
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
}
