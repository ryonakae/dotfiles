# mosh/ssh 経由の非 Aqua シェルには launchd の SSH_AUTH_SOCK が降りてこないため、
# GUI セッションが持っている socket パスを引っ張ってくる。直接ログイン時には既に
# 設定済みなので、`set -q` ガードで触らない。
if not set -q SSH_AUTH_SOCK
    set -l sock (launchctl asuser (id -u) launchctl getenv SSH_AUTH_SOCK 2>/dev/null)
    if test -n "$sock" -a -S "$sock"
        set -gx SSH_AUTH_SOCK $sock
    end
end
