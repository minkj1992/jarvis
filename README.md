# `jarvis`

> "personally, customized bot with langchain and gpt4"

<div align='center'>

![](https://user-images.githubusercontent.com/37536298/234824459-1e6f26f0-3b3b-462c-bb86-875f66879612.png)
<p><em>https://drive.google.com/file/d/1RWBf-6NVbwNbX5izffaLbD3TZnRH4jKW/view?usp=sharing</em></p>

</div>

1. Infra
    - [x] fastapi serving
    - [x] vector database: FAISS to [milvus](https://milvus.io/)
        - [x] redis-stack-server
        - [ ] pinecone
    - [ ] azure deploy
2. Auth
    - [ ] oauth2 login
    - [ ] manage quota by partner_uuid
3. Domain
    - [ ] CRUD `/room`
    - [x] Web socket chat
    - [ ] Payment
4. Etc
    - [x] dotenv python
    - [x] manage chatGPT credit issue (429)


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

## deploy
> [azure docker compose](https://learn.microsoft.com/ko-kr/azure/container-instances/tutorial-docker-compose)

**1. install az-cli**
```sh
$ brew update && brew install azure-cli
$ az login
```

2. **Generate Azure container registry**
    - `RG`: ResourceGroup
    - `acr`: Azure Container Registry
    - sku: Basic > Standard

```sh
$ az group create --name jarvisRG --location koreacentral
# only lowercase and number
$ az acr create --resource-group jarvisRG --name jarvis0acr --sku Basic
```

**3. Login to Container Registry**

```sh
$ az acr login --name jarvis0acr
Login Succeeded
```

4. **Update docker compose** `docker-compose.prod.yml` in jarvis
    - 이미지 이름 앞에 Azure Container Registry의 로그인 서버 이름인 <acrName>.azurecr.io를 붙입니다.
    - ports 매핑을 80:80으로 변경합니다.


5. **Docker push**
```sh
$ docker login
Username: minkj1992
Password: 
Login Succeeded
$ make deploy
$ az acr repository show --name jarvis0acr --repository jarvis-api
```

6. **Create an Azure context**
    - `aci`: Azure Container Instances

```sh
$ docker login azure
$ docker context create aci jarvis0context
Using only available subscription : Azure subscription 1 (f43a5e62-87da-4e9a-80db-3a94b3ab72fc)
? Select a resource group jarvisRG (koreacentral)
Successfully created aci context "jarvis0context"
$ docker context ls
```

7. Create Azure file volume
    - [create a storage account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal)
    - `Standard_LRS` is the cheapest

```sh
# https://docs.docker.com/cloud/aci-integration/#using-azure-file-share-as-volumes-in-aci-containers
jarvisRG
# create storage account name
$ az storage account create \
  --name jarvis0storage0account \
  --resource-group jarvisRG \
  --location koreacentral \
  --sku Standard_LRS \
  --kind StorageV2


$ docker --context jarvis0context volume create jarvis0redis --storage-account jarvis0storage0account

$ docker --context jarvis0context volume ls
```

8. **deploy**
    - TODO: need to handle a error below

```sh
$ make prod-up

cannot get container logs: containerinstance.ContainersClient#ListLogs: Failure responding to request: StatusCode=404 -- Original Error: autorest/azure: Service returned an error. Status=404 Code="ResourceNotFound" Message="The Resource 'Microsoft.ContainerInstance/containerGroups/jarvis0api' under resource group 'jarvisRG' was not found. For more details please go to https://aka.ms/ARMResourceNotFoundFix"
# make prod-down
```

