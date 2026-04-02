function dcb --wraps='docker compose build' --description 'docker compose build'
    docker compose build $argv
end
