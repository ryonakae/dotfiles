{
  config,
  lib,
  pkgs,
  ...
}:
let
  agentDir = "${config.home.homeDirectory}/.pi/agent";
  mutableSettings = {
    "settings.json" = ../../.pi/agent/settings.json;
    "extensions/pi-footer.json" = ../../.pi/agent/extensions/pi-footer.json;
    "extensions/pi-gpt-fast-mode/config.json" = ../../.pi/agent/extensions/pi-gpt-fast-mode/config.json;
  };
in
{
  home.file = {
    ".pi/agent/APPEND_SYSTEM.md".source = ../../.pi/agent/APPEND_SYSTEM.md;
    ".pi/agent/agent-tool-description.md".source = ../../.pi/agent/agent-tool-description.md;
    ".pi/agent/subagents.json".source = ../../.pi/agent/subagents.json;
    ".pi/agent/agents/explorer.md".source = ../../.pi/agent/agents/explorer.md;
    ".pi/agent/agents/reviewer.md".source = ../../.pi/agent/agents/reviewer.md;
    ".pi/agent/agents/worker.md".source = ../../.pi/agent/agents/worker.md;
    ".pi/agent/extensions/notification/index.ts".source =
      ../../.pi/agent/extensions/notification/index.ts;
  };

  # The standard merger follows symlinks; legacy links must not write back into this repository.
  home.activation.checkPiConfigPaths = lib.hm.dag.entryBefore [ "writeBoundary" ] (
    ''
      pi_home=$(${pkgs.coreutils}/bin/realpath -m -- ${lib.escapeShellArg config.home.homeDirectory})
    ''
    + lib.concatStrings (
      lib.mapAttrsToList (name: _: ''
        pi_settings_path=${lib.escapeShellArg "${agentDir}/${name}"}
        if [[ "$(${pkgs.coreutils}/bin/realpath -m -- "$pi_settings_path")" != "$pi_home"/${lib.escapeShellArg ".pi/agent/${name}"} ]]; then
          errorEcho "Pi config at '$pi_settings_path' resolves through a symlink; prepare a writable local file before activation."
          exit 1
        fi
      '') mutableSettings
    )
  );

  home.activation.piMutableSettings = lib.hm.dag.entryAfter [ "linkGeneration" ] (
    lib.concatStrings (
      lib.mapAttrsToList (
        name: source:
        lib.hm.generators.mkImpureConfigMerger {
          inherit pkgs;
          format = "json";
          empty = "{}";
          jqOperation = "$dynamic * $static";
          path = "${agentDir}/${name}";
          staticSettings = source;
          mode = "600";
        }
      ) mutableSettings
    )
  );
}
