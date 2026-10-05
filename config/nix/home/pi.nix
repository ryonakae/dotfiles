{ dotfilesLink, ... }:
{
  home.file = {
    ".pi/agent/settings.json".source = dotfilesLink ".pi/agent/settings.json";
    ".pi/agent/extensions/pi-footer.json".source = dotfilesLink ".pi/agent/extensions/pi-footer.json";
    ".pi/agent/extensions/pi-gpt-fast-mode/config.json".source =
      dotfilesLink ".pi/agent/extensions/pi-gpt-fast-mode/config.json";
    ".pi/agent/APPEND_SYSTEM.md".source = dotfilesLink ".pi/agent/APPEND_SYSTEM.md";
    ".pi/agent/agent-tool-description.md".source = dotfilesLink ".pi/agent/agent-tool-description.md";
    ".pi/agent/subagents.json".source = dotfilesLink ".pi/agent/subagents.json";
    ".pi/agent/agents/explorer.md".source = dotfilesLink ".pi/agent/agents/explorer.md";
    ".pi/agent/agents/reviewer.md".source = dotfilesLink ".pi/agent/agents/reviewer.md";
    ".pi/agent/agents/worker.md".source = dotfilesLink ".pi/agent/agents/worker.md";
    ".pi/agent/extensions/notification/index.ts".source =
      dotfilesLink ".pi/agent/extensions/notification/index.ts";
  };
}
