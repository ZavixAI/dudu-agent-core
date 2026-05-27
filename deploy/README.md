# dudu-agent-core Deploy

部署相关文件统一放在 `deploy/` 下：

- `deploy/images/`: Dockerfile 和入口脚本
- `deploy/dev/`: 开发环境 Docker Compose 与环境变量模板
- `deploy/prod/`: 生产环境 Docker Compose 与环境变量模板
- `deploy/test/`: 测试环境 Docker Compose 与环境变量模板

当前 Compose 只部署一个服务：`dudu-agent-core`。MySQL 作为外部依赖，通过各环境 `.env` 中的 `DUDU_MYSQL_*` 变量连接。

## Docker Compose

先按目标环境创建 `.env`：

```bash
cp deploy/dev/.env.example deploy/dev/.env
cp deploy/prod/.env.example deploy/prod/.env
cp deploy/test/.env.example deploy/test/.env
```

推荐通过环境入口部署：

```bash
deploy/compose.sh up -d --build
deploy/compose.sh dev up -d --build
deploy/compose.sh prod up -d --build
deploy/compose.sh test up -d --build
```

`deploy/compose.sh` 默认使用 `prod` 环境；也可以通过第一个参数指定 `dev`、`prod` 或 `test`。脚本默认优先读取 `deploy/<env>/.env`；如果该文件不存在，则回退读取仓库根目录 `.env`。也可以通过 `ENV_FILE=/path/to/.env` 显式指定配置文件。

也可以直接指定对应 compose 文件：

```bash
docker compose --env-file deploy/dev/.env -f deploy/dev/docker-compose.yml up -d --build
docker compose --env-file deploy/prod/.env -f deploy/prod/docker-compose.yml up -d --build
docker compose --env-file deploy/test/.env -f deploy/test/docker-compose.yml up -d --build
```

默认宿主机端口：

- `prod`: `DUDU_SERVER_PORT=30352`
- `dev`: `DUDU_SERVER_PORT=31080`
- `test`: `DUDU_SERVER_PORT=32080`

服务健康检查访问容器内 `GET /health`。
