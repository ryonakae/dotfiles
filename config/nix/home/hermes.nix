{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:
let
  home = config.home.homeDirectory;
  hermes = inputs.hermes-agent.packages.${pkgs.stdenv.hostPlatform.system}.default;
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
          [ "#!/bin/bash" ''run-with-agent-env.sh" safehouse '' "  hermes --profile " ]
          [
            "#!${pkgs.runtimeShell}"
            ''run-with-agent-env.sh" ${lib.getExe pkgs.agent-safehouse} ''
            "  ${hermes}/bin/hermes --profile "
          ]
          (builtins.readFile (../../.config/agent-safehouse + "/safe-hermes-${name}.sh"));
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
          PATH = "${home}/.local/bin:${config.home.path}/bin:/run/current-system/sw/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin";
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
      builtins.readFile ../../.config/hermes/check-stopped.sh
    );
  };
in
{
  home.file = {
    ".hermes/SOUL.md".source = ../../.hermes/SOUL.md;
    ".hermes/services/docker-compose.yml".source = ../../.hermes/services/docker-compose.yml;
  };
  xdg.configFile = {
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

  home.activation.checkHermesServices = lib.hm.dag.entryBefore [ "writeBoundary" ] (
    ''
      ${checkStopped}
      hermes_home=$(${pkgs.coreutils}/bin/realpath -m -- ${lib.escapeShellArg home})
    ''
    + lib.concatMapStringsSep "\n" (name: ''
      hermes_plist=${lib.escapeShellArg "${home}/Library/LaunchAgents/ai.hermes.${name}.plist"}
      if [[ "$(${pkgs.coreutils}/bin/realpath -m -- "$hermes_plist")" != "$hermes_home/Library/LaunchAgents/ai.hermes.${name}.plist" || -L "$hermes_plist" ]]; then
        errorEcho "Hermes plist path resolves through a symlink; prepare the destination before activation."
        exit 1
      fi
      if [[ -e "$hermes_plist" ]]; then
        if [[ ! -f "$hermes_plist" || ! -O "$hermes_plist" ]]; then
          errorEcho "Hermes plist is not a user-owned regular file; refusing replacement."
          exit 1
        fi
        if ! ${pkgs.diffutils}/bin/cmp -s "$hermes_plist" ${plists.${name}}; then
          if [[ -z "''${oldGenPath:-}" ]] || ! ${pkgs.diffutils}/bin/cmp -s "$hermes_plist" "$oldGenPath/hermes-launch-agents/ai.hermes.${name}.plist"; then
            errorEcho "Unmanaged or modified Hermes plist: back it up explicitly before activation."
            exit 1
          fi
        fi
      fi
    '') services
  );

  home.activation.installHermesPlists = lib.hm.dag.entryAfter [ "linkGeneration" ] (
    ''
      ${checkStopped}
    ''
    + lib.concatMapStringsSep "\n" (name: ''
      run ${pkgs.coreutils}/bin/install -D -m 444 ${plists.${name}} ${lib.escapeShellArg "${home}/Library/LaunchAgents/ai.hermes.${name}.plist"}
    '') services
  );
}
