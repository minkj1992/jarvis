# jarvis

> "personally, customized bot with langchain and gpt4"

<div align='center'>

<h4>click to play</h4>

[![](https://user-images.githubusercontent.com/37536298/234824459-1e6f26f0-3b3b-462c-bb86-875f66879612.png)]("https://drive.google.com/file/d/1RWBf-6NVbwNbX5izffaLbD3TZnRH4jKW/view?usp=sharing")

</div>

1. Infra
    - [ ] fastapi serving
    - [ ] vector database: FAISS to [milvus](https://milvus.io/) or redis
    - [ ] azure serving
2. Auth
    - [ ] oauth2 login
    - [ ] manage quota
3. Domain
    - [ ] POST / DELETE `/room`
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
