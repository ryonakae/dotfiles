function dcu --wraps='docker-compose up' --description 'docker-compose up'
    docker-compose up $argv
end
