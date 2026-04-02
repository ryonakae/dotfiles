function dcd --wraps='docker compose down' --description 'docker compose down'
    docker compose down $argv
end
