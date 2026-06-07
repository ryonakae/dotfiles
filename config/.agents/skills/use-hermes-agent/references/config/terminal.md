# ターミナルバックエンド

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#terminal-backend-configuration

6 種類: `local`（デフォルト）、`docker`、`ssh`、`modal`、`daytona`、`singularity`

```yaml
terminal:
  backend: local           # local | docker | ssh | modal | daytona | singularity
  cwd: "."
  timeout: 180
  env_passthrough: []
  persistent_shell: false   # SSH ではデフォルト true
```

## Docker バックエンド

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_mount_cwd_to_workspace: false
  docker_forward_env: ["GITHUB_TOKEN"]
  docker_volumes:
    - "/home/user/projects:/workspace/projects"
  container_cpu: 1
  container_memory: 5120     # MB
  container_disk: 51200      # MB
  container_persistent: true
```

## SSH バックエンド

```yaml
terminal:
  backend: ssh
  persistent_shell: true
# .env に設定:
# TERMINAL_SSH_HOST=my-server.example.com
# TERMINAL_SSH_USER=ubuntu
# TERMINAL_SSH_KEY=/path/to/key
```
