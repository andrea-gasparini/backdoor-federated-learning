# Backdoor Federated Learning

This repository hosts the project on the backdoor attack in a Federated learning setting using the [FATE framework](https://github.com/FederatedAI/FATE).
This project has been developed during the A.Y. 2021-2022 for the [Advanced Topics in Security and Privacy](https://gitlab.com/atsp2021) course @ University of Groningen.

The details about our work and the obtained results can be found inside the [report](report/report.pdf).

## Installation

First things first, clone this repository and then move into it.

```bash
git clone https://gitlab.com/atsp2021/backdoor-federated-learning.git && \
cd backdoor-federated-learning
```

In order to slightly reduce the possibility of encountering problems we are going to install FATE using Docker. So be sure to have [Docker installed](https://docs.docker.com/get-docker/) and to run the following docker commands as a root user (or to follow the [Manage Docker as a non-root user](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) guide).

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

```bash
tar -xzvf docker_standalone_fate_1.6.1.tar.gz
docker load < docker_standalone_fate_1.6.1/fate.tar
```

And run a new docker container with the FATE image. The current directory is going to be binded to `/fate/backdoor-attack` inside the container, so be sure that `$(pwd)` corresponds to the root of our repository.

```bash
docker run -d --name fate -p 8080:8080 \
--mount type=bind,source="$(pwd),target=/fate/backdoor-attack" fate:1.6.1
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

And, in order to setup Pipeline FATE jobs, initialize FATE-Flow CLI providing server ip/port information of deployed FATE-Flow.

```bash
flow init --ip 127.0.0.1 --port 9380
pipeline init --ip 127.0.0.1 --port 9380
```

## Usage

The following usage examples are supposed to be executed from the docker container shell, inside the `/fate/backdoor-attack` directory.

In order to run a single experiment you can execute the `run_experiment.py` script, specifying the poison percentage with the `--poison-percentage` option.

```bash
python src/run_experiment.py --poison-percentage 0.5
```

To run multiple experiments and reproduce the results shown in the [report](report/report.pdf) you can simply execute the `run_experiment.py` script without any argument.

```bash
python src/run_experiment.py
```

## Authors

- [Andrea Gasparini](https://github.com/andrea-gasparini)
- [Arjan Tilstra](https://github.com/ArjanTilstra)
- [Gerrit Luimstra](https://github.com/GerritLuimstra)
