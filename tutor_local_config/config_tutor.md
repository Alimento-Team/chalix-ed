# To config ~/.local/share/tutor/config.yml

In a particular environment, you should find the tutor config dir by running the following command:

```bash
tutor config printroot
```

This README assumes that the tutor config dir is `~/.local/share/tutor`.

## 1. Dockerfile
This Dockerfile is used to copy a local directory of `chalix-edu` source code to the tutor container. The source code is spcified by using the Docker build arg `CHALIX_DIR`.

The Dockerfile should be placed at `~/.local/share/tutor/env/build/openedx/Dockerfile`.

Then you can build your local image by using tutor command:

```bash
tutor images build openedx --build-arg CHALIX_DIR=/home/alimento/dungdl/code/chalix-ed
```

## 2. config.yml
The config file is used to specifies customized configurations and setup for `tutor` local.
It should be placed at `~/.local/share/tutor/config.yml`.

## 3. env/local
This directory contains overrided command for local `docker-compose` that runs the `tutor local`. It should be placed at `~/.local/share/tutor/env/local`.

[] Currently, this does not handle the case where `caddy` container should join the `charlix-network` in order to connect to relevant database services. A workaround is to manually add the `caddy` container to the network by running the following command:

```bash
docker network connect chalix-network tutor_local-caddy-1
```

## 4. Caddyfile
This file is used to configure the `caddy` server. It should be placed at `~/.local/share/tutor/env/build/openedx/Caddyfile`.