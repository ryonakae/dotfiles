{
  config,
  hermes,
  lib,
  pkgs,
  ...
}:
let
  home = config.home.homeDirectory;
  services = [
    "gateway"
    "dashboard"
  ];
  wrappers = lib.genAttrs services (
    name:
    pkgs.writeTextFile {
      name = "safe-hermes-${name}.sh";
      executable = true;
      text =
        lib.replaceStrings
          [ "#!/bin/bash" ''"$HOME/.local/libexec/hermes"'' ]
          [ "#!${pkgs.runtimeShell}" ''"${hermes}/bin/hermes"'' ]
          (builtins.readFile (../../config/.config/agent-safehouse + "/safe-hermes-${name}.sh"));
    }
  );
  plists = lib.genAttrs services (
    name:
    pkgs.writeText "ai.hermes.${name}.plist" (
      lib.generators.toPlist { escape = true; } {
        Label = "ai.hermes.${name}";
        ProgramArguments = [ "${wrappers.${name}}" ];
        WorkingDirectory = "${home}/.hermes";
        EnvironmentVariables = {
          HOME = home;
          HERMES_HOME = "${home}/.hermes";
          PATH = "${home}/.local/bin:${home}/.local/share/mise/shims:${config.home.path}/bin:/run/current-system/sw/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin";
        };
        Disabled = true;
        RunAtLoad = true;
        # Native dashboard stop must not race an automatic respawn.
        KeepAlive = false;
        StandardOutPath = "${home}/.hermes/logs/${name}.log";
        StandardErrorPath = "${home}/.hermes/logs/${name}.error.log";
      }
    )
  );
  definitions = pkgs.runCommand "hermes-launch-agents" { } (
    "mkdir -p $out\n"
    + lib.concatMapStringsSep "\n" (name: "cp ${plists.${name}} $out/ai.hermes.${name}.plist") services
  );
  checkStopped = pkgs.writeTextFile {
    name = "hermes-check-stopped";
    executable = true;
    text = lib.replaceStrings [ "#!/bin/bash" ] [ "#!${pkgs.runtimeShell}" ] (
      builtins.readFile ../../config/.config/hermes/check-stopped.sh
    );
  };
  comparePlists = ''
    hermes_changed=()
    hermes_home=$(${pkgs.coreutils}/bin/realpath -m -- ${lib.escapeShellArg home})
    for name in ${lib.escapeShellArgs services}; do
      hermes_plist=${lib.escapeShellArg "${home}/Library/LaunchAgents"}/ai.hermes.$name.plist
      if [[ "$(${pkgs.coreutils}/bin/realpath -m -- "$hermes_plist")" != "$hermes_home/Library/LaunchAgents/ai.hermes.$name.plist" || -L "$hermes_plist" ]]; then
        echo "Hermes: plist path resolves through a symlink: $hermes_plist" >&2
        exit 1
      fi
      if [[ ! -e "$hermes_plist" ]]; then
        hermes_changed+=("$name")
        continue
      fi
      if [[ ! -f "$hermes_plist" || ! -O "$hermes_plist" || ! -r "$hermes_plist" ]]; then
        echo "Hermes: plist is not a readable user-owned regular file: $hermes_plist" >&2
        exit 1
      fi
      if ${pkgs.diffutils}/bin/cmp -s "$hermes_plist" ${definitions}/ai.hermes.$name.plist; then
        continue
      else
        hermes_cmp_status=$?
        if [[ "$hermes_cmp_status" != 1 ]]; then
          echo "Hermes: cannot compare plist: $hermes_plist" >&2
          exit 1
        fi
      fi
      hermes_changed+=("$name")
    done
  '';
  checkActivation = pkgs.writeShellScript "hermes-check-activation" ''
    set -euo pipefail
    ${comparePlists}
    if [[ ''${#hermes_changed[@]} -gt 0 ]]; then
      ${checkStopped}
    fi
  '';
in
{
  home.file.".local/libexec/hermes".source = "${hermes}/bin/hermes";
  xdg.configFile = {
    "hermes/check-activation.sh" = {
      source = checkActivation;
      executable = true;
    };
    "hermes/check-stopped.sh" = {
      source = checkStopped;
      executable = true;
    };
  }
  // lib.listToAttrs (
    map (name: {
      name = "agent-safehouse/safe-hermes-${name}.sh";
      value = {
        source = wrappers.${name};
        executable = true;
      };
    }) services
  );

  home.extraBuilderCommands = ''
    ln -s ${definitions} $out/hermes-launch-agents
  '';

  home.activation.checkHermesServices = lib.hm.dag.entryBefore [ "writeBoundary" ] ''
    ${comparePlists}
    if [[ ''${#hermes_changed[@]} -gt 0 ]]; then
      for name in "''${hermes_changed[@]}"; do
        hermes_plist=${lib.escapeShellArg "${home}/Library/LaunchAgents"}/ai.hermes.$name.plist
        if [[ -e "$hermes_plist" ]]; then
          if [[ -z "''${oldGenPath:-}" ]] || ! ${pkgs.diffutils}/bin/cmp -s "$hermes_plist" "$oldGenPath/hermes-launch-agents/ai.hermes.$name.plist"; then
            errorEcho "Unmanaged or modified Hermes plist: back it up explicitly before activation."
            exit 1
          fi
        fi
      done
    fi
    ${checkActivation}
  '';

  home.activation.installHermesPlists = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    ${comparePlists}
    if [[ ''${#hermes_changed[@]} -gt 0 ]]; then
      ${checkStopped}
      for name in "''${hermes_changed[@]}"; do
        run ${pkgs.coreutils}/bin/install -D -m 444 ${definitions}/ai.hermes.$name.plist ${lib.escapeShellArg "${home}/Library/LaunchAgents"}/ai.hermes.$name.plist
      done
    fi
  '';
}
