# KRILOG


```bash
# building the image
docker build -t sysnetcz/krilog .

# starting up a container
docker run --name krilog -p 8888:8000 -d sysnetcz/krilog

# starting up a container
docker run --name krilog -v ./data:/opt/krilog/data -p 8899:8000 -d sysnetcz/krilog

```