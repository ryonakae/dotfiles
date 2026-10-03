{ pkgs, inputs, ... }:
{
  home.packages = with pkgs; [
    actionlint
    age
    agent-browser
    agent-safehouse
    awscli2
    cocoapods
    ctx7
    dotenvx
    fastlane
    fd
    ffmpeg
    fzf
    gh
    git
    git-lfs
    gomi
    imagemagick
    jq
    keifu
    mas
    mkcert
    terminal-notifier
    tmux
    tree
    usage
    uv
    vim
    worktrunk
    yazi
    zellij

    bun
    nodejs_22
    python311
    ruby_3_3

    inputs.self.packages.aarch64-darwin.claude-code
    inputs.self.packages.aarch64-darwin.codex
    inputs.self.packages.aarch64-darwin.opencode
    inputs.self.packages.aarch64-darwin.pi-coding-agent
  ];
}
