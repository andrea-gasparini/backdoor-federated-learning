# Backdoor Federated Learning

This repository hosts the project on the backdoor attack in a Federated learning setting using the [FATE framework](https://github.com/FederatedAI/FATE).
This project has been developed during the A.Y. 2021-2022 for the [Advanced Topics in Security and Privacy](https://gitlab.com/atsp2021) course @ University of Groningen.

## Installation

In order to slightly reduce the possibility of encountering problems we are going to install FATE using Docker, as suggested in the [FATE Stand-alone Deployment Guide](https://github.com/FederatedAI/FATE/blob/master/standalone-deploy/README.md).

We suggest to use FATE version `1.6.1`, for which we provide the following mirror download.

```
wget http://gasparini.cloud/FATE/docker_standalone_fate_1.6.1.tar.gz
```

Other versions can be downloaded from the original repository replacing `${version}` below with the real version you want to use.
Note: This option could take a lot of time (download is from China), so this is not recommended.

```bash
wget https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/docker_standalone_fate_${version}.tar.gz
```

Once we have the docker archive file we can proceed with the actual installation of the docker image.
Note: Before running the following docker commands be sure to be a root user or to follow [this guide](https://docs.docker.com/engine/install/linux-postinstall/) beforehand.

```bash
tar -xzvf docker_standalone_fate_1.6.1.tar.gz
docker load < docker_standalone_fate_1.6.1/fate.tar
```

And run a new docker container with the FATE image.

```bash
docker run -d --name fate -p 8080:8080 fate:1.6.1
```

Now create a new shell to interact with the Docker container and the FATE environment.

```bash
CONTAINER_ID=`docker ps -aqf "name=fate"`
docker exec -t -i ${CONTAINER_ID} bash
```

To conveniently interact with FATE, it is recommended to also install [FATE-Client](https://github.com/FederatedAI/FATE/blob/master/python/fate_client) and [FATE-Test](https://github.com/FederatedAI/FATE/blob/master/python/fate_test) inside the container (through the new shell created in the previous code block).

```bash
pip install fate-client fate-test
```

And, in order to setup Pipeline FATE jobs, to also provide server ip/port information of deployed FATE-Flow.

```bash
pipeline init --ip 127.0.0.1 --port 9380
```

## Bind host directories with the Docker container

Move to the root directory of the [FATE repository](https://github.com/FederatedAI/FATE) and run the following command in order to bind the directories `/examples` and `/python` to the respective Docker container ones.

```bash
docker run -p 8080:8080 -d --name fate --mount type=bind,source="$(pwd)/examples,target=/fate/examples" --mount type=bind,source="$(pwd)/python,target=/fate/python" fate:1.6.1
```

## Authors

- [Andrea Gasparini](https://github.com/andrea-gasparini)
- [Arjan Tilstra](https://github.com/ArjanTilstra)
- [Gerrit Luimstra](https://github.com/GerritLuimstra)
