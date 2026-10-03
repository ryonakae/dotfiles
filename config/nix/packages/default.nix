{ pkgs }:
{
  claude-code = import ./claude-code.nix { inherit pkgs; };
  codex = import ./codex.nix { inherit pkgs; };
  opencode = import ./opencode.nix { inherit pkgs; };
  pi-coding-agent = import ./pi-coding-agent.nix { inherit pkgs; };
}
