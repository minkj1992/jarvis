# jarvis

> "personally, customized bot with langchain and gpt4"


<div align="center">

<video  preload="auto" controls>
   <source src="https://drive.google.com/uc?export=download&id=1RWBf-6NVbwNbX5izffaLbD3TZnRH4jKW" type='video/mp4'>
</video>

<video  width="80%" controls autoplay>
    <source src="https://drive.google.com/file/d/1RWBf-6NVbwNbX5izffaLbD3TZnRH4jKW/view" type="video/mp4">    
</video>

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
