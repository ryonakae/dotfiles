function dri --wraps='docker rmi' --description 'docker rmi'
    docker rmi $argv
end
