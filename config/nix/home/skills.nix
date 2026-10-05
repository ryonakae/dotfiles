{
  config,
  dotfilesLink,
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
  external = {
    agent-browser = {
      from = "agent-browser";
      path = "skills/agent-browser";
    };
    agent-device = {
      from = "agent-device";
      path = "skills/agent-device";
    };
    cognitive-rhythm-writing = {
      from = "tech-writing";
      path = "skills/cognitive-rhythm-writing";
    };
    cua-driver = {
      from = "cua-driver";
      path = "libs/cua-driver/rust/Skills/cua-driver";
    };
    find-docs = {
      from = "find-docs";
      path = "skills/find-docs";
    };
    herdr = {
      from = "herdr";
      path = "skills/herdr";
    };
    japanese-tech-writing = {
      from = "tech-writing";
      path = "skills/japanese-tech-writing";
    };
    readme-creator = {
      from = "readme-creator";
      path = "skills/readme-creator";
    };
    readme-i18n = {
      from = "readme-i18n";
      path = "skills/readme-i18n";
    };
    skill-creator = {
      from = "skill-creator";
      path = "skills/skill-creator";
    };
    stop-slop = {
      from = "stop-slop";
      path = ".";
    };
    stop-slop-ja = {
      from = "stop-slop-ja";
      path = ".";
    };
    tdd = {
      from = "tdd";
      path = "skills/engineering/tdd";
    };
    worktrunk = {
      from = "worktrunk";
      path = "skills/worktrunk";
    };
  };
in
{
  programs.agent-skills = {
    enable = true;
    sources = lib.genAttrs (lib.unique (map (skill: skill.from) (lib.attrValues external))) (name: {
      input = "skills-${name}";
      # Explicit selection avoids scanning unrelated skills in each repository.
      filter.maxDepth = 0;
    });
    skills.explicit = lib.mapAttrs (
      name: skill:
      skill
      // {
        agents =
          lib.optional (!(builtins.hasAttr name shared)) "agents"
          ++ lib.optional (!(builtins.hasAttr name claude)) "claude";
      }
    ) external;
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
