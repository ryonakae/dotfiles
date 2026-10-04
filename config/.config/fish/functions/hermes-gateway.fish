function hermes-gateway --description "Manage the Nix-owned Hermes gateway"
    switch "$argv[1]"
        case start stop restart status
            if test (count $argv) -ne 1
                echo "Usage: hermes-gateway {start|stop|restart|status|update}" >&2
                return 2
            end
            command "$HOME/.config/hermes/hermes-service.py" $argv[1] gateway
            return $status
        case update
            echo "Hermes is managed by Nix; no service was stopped or updated." >&2
            echo "In the dotfiles repository: scripts/dotfiles.sh update hermes-agent; then scripts/dotfiles.sh build." >&2
            echo "Apply the reviewed generation only after both services are safely stopped; restart explicitly after approval." >&2
            return 1
        case '*'
            echo "Usage: hermes-gateway {start|stop|restart|status|update}" >&2
            return 2
    end
end
