function gemini --description "Run Gemini through Agent Safehouse"
    set -lx NO_BROWSER true
    safe gemini --yolo $argv
end
