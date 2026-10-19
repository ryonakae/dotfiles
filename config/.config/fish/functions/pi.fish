function pi --description "Run Pi through Agent Safehouse"
    set -lx PI_TELEMETRY 0
    set -lx GIT_OPTIONAL_LOCKS 0
    # Herdr のペインには SSH_* が渡らず、mosh 越しでも接続先 Mac のクリップボードへ書かれてしまう
    set -lx PI_CLIPBOARD_OSC52 1
    safe pi $argv
end
