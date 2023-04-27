# jarvis

> "personally, customized bot with langchain and gpt4"


https://user-images.githubusercontent.com/37536298/234813177-bbf17792-77c4-4a33-a394-d613c0e85e86.mov


1. Infra
    - [ ] fastapi serving
    - [ ] vector database: FAISS to [milvus](https://milvus.io/)
    - [ ] cloud flare serving
2. Auth
    - [ ] oauth2 login
    - [ ] manage quota
3. Domain
    - [ ] POST / DELETE `/room`
    - [ ] Web socket chat
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


## refs
