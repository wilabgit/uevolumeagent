Before deploying the Ollama Docker Compose container on the Jetson AGX Orin, install the NVIDIA Container Toolkit and configure Docker to enable GPU access, following the official documentation: https://docs.ollama.com/docker

To start the Ollama Docker Compose container, execute the following commands:

```bash
cd ollama-docker
docker compose -f docker-compose.yml up -d
```
The `up -d` command starts the services in the background.
