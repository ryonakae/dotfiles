{ pkgs, ... }:
let
  agentInstructions = ../../.agents/AGENTS.md;
in
{
  home.file = {
    ".agents/AGENTS.md".source = agentInstructions;
    ".claude/CLAUDE.md".source = agentInstructions;
    ".codex/AGENTS.md".source = agentInstructions;
    ".gemini/GEMINI.md".source = agentInstructions;
    ".pi/agent/AGENTS.md".source = agentInstructions;

    ".agents/hooks/notification.sh" = {
      source = ../../.agents/hooks/notification.sh;
      executable = true;
    };
    ".claude/hooks/notification.sh" = {
      source = ../../.claude/hooks/notification.sh;
      executable = true;
    };
    ".codex/hooks/notification.sh" = {
      source = ../../.codex/hooks/notification.sh;
      executable = true;
    };
    ".gemini/hooks/notification.sh" = {
      source = ../../.gemini/hooks/notification.sh;
      executable = true;
    };
  };

  xdg.configFile = {
    "ghostty/config".source = ../../.config/ghostty/config;
    "worktrunk/config.toml".source = ../../.config/worktrunk/config.toml;
    "husky/init.sh".source = ../../.config/husky/init.sh;

    "yazi/yazi.toml".source = ../../.config/yazi/yazi.toml;
    "yazi/keymap.toml".source = ../../.config/yazi/keymap.toml;
    "yazi/init.lua".source = ../../.config/yazi/init.lua;
    "yazi/plugins/git.yazi".source = pkgs.yaziPlugins.git;
    "yazi/plugins/smart-enter.yazi".source = pkgs.yaziPlugins.smart-enter;
    "yazi/plugins/full-border.yazi".source = pkgs.yaziPlugins.full-border;
    "yazi/plugins/smart-leave.yazi/main.lua".source =
      ../../.config/yazi/plugins/smart-leave.yazi/main.lua;
  };
}
