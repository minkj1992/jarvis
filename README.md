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

## deploy

```sh
$ make prod-down && make deploy
```

## ssh

```sh
$ make ssh
```


## refs
- [wss](https://github.com/tiangolo/fastapi/issues/3008#issuecomment-1031293342)
- 