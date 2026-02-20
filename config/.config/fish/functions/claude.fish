function claude --description "Start claude with skip permissions"
  if test (count $argv) -eq 0
    command claude --dangerously-skip-permissions
  else
    command claude $argv
  end
end
