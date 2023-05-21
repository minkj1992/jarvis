# `jarvis`

> "personally, customized bot with langchain and gpt4"



<div align='center'>
<h4>1. Swagger</h4>
<img src="docs/swagger.png" >
<img src="docs/swagger2.png" >

<h4>2. Vectorstore redis</h4>
<img src="docs/redis-commander.png" >
<img src="docs/redis-commander2.png" >

<h4>3. Use case</h4>
</div>


<table width="100%" border="0">
  <tr>    
  <td><img src="docs/wss1.png" alt="" align="left" /></td>
  <td><img src="docs/wss2.png" alt="" align="right"/></td>
  </tr>
</table>

<div align="center">
    <img width="40%" src="docs/kakao.jpeg" alt="" align="center" />
</div>


1. Infra
    - [x] fastapi serving
    - [x] vector database: FAISS to [milvus](https://milvus.io/)
        - [x] redis-stack-server
        - [ ] pinecone
    - [x] azure deploy
2. Auth
    - [ ] oauth2 login
    - [ ] manage quota by partner_uuid
3. Domain
    - [x] CRUD `/room`
    - [x] Web socket chat
    - [ ] Payment
4. Etc
    - [x] dotenv python
    - [x] manage chatGPT credit issue (429)
    - [x] nginx ssl with let's encrypt (auto renewal by 3month)
    - [x] deploy on azure
5. Todo
    - kakao callback
    - prompt template
    - issue handling
    - logger monitoring

## init

```sh
$ poetry init
$ poetry env use python3.8
$ poetry add langchain faiss-cpu
```

- vscode setting

```sh
$ poetry config virtualenvs.in-project true
$ poetry config virtualenvs.path "./.venv"
```

## local

```sh
$ make up
```

## deploy with azure vm


```sh
$ make prod-down && make deploy
```

## ssh

```sh
$ make ssh
```


## refs
- [wss](https://github.com/tiangolo/fastapi/issues/3008#issuecomment-1031293342)


## deploy with Google Cloud vm
> https://lemontia.tistory.com/1074

1. pre-install: gcloud-cli: https://cloud.google.com/sdk/docs/install?hl=en
2. run script to deploy vm

```bash
$ ./deploy_gcp_vm.sh tidy-amplifier-387210 asia-northeast3-a e2-standard-4 jarvis-instance
```
3. Set Nameserver (i.g [가비아](https://customer.gabia.com/manual/domain/286/991))

4. Git 
5. [docker install on ubuntu](https://docs.docker.com/engine/install/ubuntu/)

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker ${USER}
```

- docker build with pip install
    - [solution](https://blockchainstudy.tistory.com/59)

```
#0 136.5 ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device
#0 136.5
#0 136.7 WARNING: You are using pip version 22.0.4; however, version 23.1.2 is available.
#0 136.7 You should consider upgrading via the '/usr/local/bin/python -m pip install --upgrade pip' command.
```
