function dce --wraps='docker compose exec' --description 'docker compose exec'
    docker compose exec $argv
end
