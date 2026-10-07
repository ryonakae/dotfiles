function pi --description "Run Pi through Agent Safehouse"
    set -lx PI_TELEMETRY 0
    set -lx GIT_OPTIONAL_LOCKS 0
    safe pi $argv
end
