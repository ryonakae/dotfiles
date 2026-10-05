{ dotfilesLink, pkgs, ... }:
let
  agentInstructions = dotfilesLink ".agents/AGENTS.md";
in
{
  home.file = {
    ".vimrc".source = dotfilesLink ".vimrc";
    ".agents/AGENTS.md".source = agentInstructions;
    ".claude/CLAUDE.md".source = agentInstructions;
    ".codex/AGENTS.md".source = agentInstructions;
    ".gemini/GEMINI.md".source = agentInstructions;
    ".pi/agent/AGENTS.md".source = agentInstructions;
    ".claude/settings.json".source = dotfilesLink ".claude/settings.json";

    ".agents/hooks/notification.sh".source = dotfilesLink ".agents/hooks/notification.sh";
    ".claude/hooks/herdr-agent-state.sh" = {
      source = "${pkgs.herdr.src}/src/integration/assets/claude/herdr-agent-state.sh";
      executable = true;
    };
    ".claude/hooks/notification.sh".source = dotfilesLink ".claude/hooks/notification.sh";
    ".codex/hooks/notification.sh".source = dotfilesLink ".codex/hooks/notification.sh";
    ".gemini/hooks/notification.sh".source = dotfilesLink ".gemini/hooks/notification.sh";
  };

  xdg.configFile = {
    "ghostty/config".source = dotfilesLink ".config/ghostty/config";
    "worktrunk/config.toml".source = dotfilesLink ".config/worktrunk/config.toml";
    "husky/init.sh".source = dotfilesLink ".config/husky/init.sh";
    "zed/settings.json".source = dotfilesLink ".config/zed/settings.json";
    "opencode/opencode.json".source = dotfilesLink ".config/opencode/opencode.json";
    "pi-auto-name/config.json".source = dotfilesLink ".config/pi-auto-name/config.json";

    "herdr/config.toml".source = dotfilesLink ".config/herdr/config.toml";
    "herdr/plugins/config/ryonakae.agent-context/config.toml".source =
      dotfilesLink ".config/herdr/plugins/config/ryonakae.agent-context/config.toml";
    "herdr/plugins/config/worktrunk/config.toml".source =
      dotfilesLink ".config/herdr/plugins/config/worktrunk/config.toml";
    "herdr/scripts/focus-pane-or-tab.sh".source =
      dotfilesLink ".config/herdr/scripts/focus-pane-or-tab.sh";
    "herdr/scripts/normalize-clipboard.py".source =
      dotfilesLink ".config/herdr/scripts/normalize-clipboard.py";

    "yazi/yazi.toml".source = dotfilesLink ".config/yazi/yazi.toml";
    "yazi/keymap.toml".source = dotfilesLink ".config/yazi/keymap.toml";
    "yazi/init.lua".source = dotfilesLink ".config/yazi/init.lua";
    "yazi/plugins/git.yazi".source = pkgs.yaziPlugins.git;
    "yazi/plugins/smart-enter.yazi".source = pkgs.yaziPlugins.smart-enter;
    "yazi/plugins/full-border.yazi".source = pkgs.yaziPlugins.full-border;
    "yazi/plugins/smart-leave.yazi/main.lua".source =
      dotfilesLink ".config/yazi/plugins/smart-leave.yazi/main.lua";
  };
}
