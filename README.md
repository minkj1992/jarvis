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

1. **install az-cli**

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
$ az acr create --resource-group jarvisRG --name jarvisgptacr --sku Basic
```

3. **Login to Container Registry**

```sh
$ az acr login --name jarvisgptacr
Login Succeeded
```

4. **Update docker compose** `docker-compose.prod.yml` in jarvis
    - change docker compose image with `<acrName>.azurecr.io/<image_name>:<tag>`


5. **Docker push**
```sh
$ docker login
Username: minkj1992
Password: 
Login Succeeded
$ make deploy
$ az acr repository show --name jarvisgptacr --repository jarvis-api
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

7. **Create Azure file volume**
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


```sh
$ make prod-up
# make prod-down
```


## debug

```
az container show --resource-group jarvisRG --name jarvis --output table
```

```
az container logs --resource-group jarvisRG --name jarvis --container-name jarvis-redis
az container logs --resource-group jarvisRG --name jarvis --container-name jarvis-api
az container logs --resource-group jarvisRG --name jarvis --container-name aci--dns--sidecar
```


- [acr task](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-tutorial-quick-task)

```
RES_GROUP=jarvisRG
ACR_NAME=jarvisgptacr
IMAGE_NAME_TAG_=jarvis_app:v1
AKV_NAME=$ACR_NAME-vault



az acr build --registry $ACR_NAME --image jarvisgptacr.azurecr.io/$IMAGE_NAME_TAG_ .

# Create a key vault
az keyvault create --resource-group $RES_GROUP --name $AKV_NAME
# Create service principal, store its password in AKV (the registry *password*)
az keyvault secret set \
  --vault-name $AKV_NAME \
  --name $ACR_NAME-pull-pwd \
  --value $(az ad sp create-for-rbac \
                --name $ACR_NAME-pull \
                --scopes $(az acr show --name $ACR_NAME --query id --output tsv) \
                --role acrpull \
                --query password \
                --output tsv)

# Store service principal ID in AKV (the registry *username*)
az keyvault secret set \
    --vault-name $AKV_NAME \
    --name $ACR_NAME-pull-usr \
    --value $(az ad sp list --display-name $ACR_NAME-pull --query '[].appId' --output tsv)

az container create \
    --resource-group $RES_GROUP \
    --name acr-tasks \
    --image $ACR_NAME.azurecr.io/$IMAGE_NAME_TAG_ \
    --registry-login-server $ACR_NAME.azurecr.io \
    --registry-username $(az keyvault secret show --vault-name $AKV_NAME --name $ACR_NAME-pull-usr --query value -o tsv) \
    --registry-password $(az keyvault secret show --vault-name $AKV_NAME --name $ACR_NAME-pull-pwd --query value -o tsv) \
    --dns-name-label acr-tasks-$ACR_NAME \
    --query "{FQDN:ipAddress.fqdn}" \
    --output table


# verify deployment
az container attach --resource-group $RES_GROUP --name acr-tasks
```

## 

```
curl -L <https://raw.githubusercontent.com/wmnnd/nginx-certbot/master/init-letsencrypt.sh> > init-letsencrypt.sh
chmod +x init-letsencrypt.sh
vi init-letsencrypt.sh // 도메인, 이메일, 디렉토리 수정
sudo ./init-letsencrypt.sh // 인증서 발급  

```
