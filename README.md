# jarvis

> "personally, customized bot with langchain and gpt4"

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

## run

**generate embedding model**

```sh
$ poetry run python learn.py
```

**ask query to gpt**

```sh
$ poetry run python ask.py \
--question='What is ICP?'

> Finished chain.
Answer:  ICP stands for Interchain Protocol and is a blockchain protocol that can host fully-on chain dapps.

Sources: https://minkj1992.github.io/categories/icp/, https://minkj1992.github.io/ledger_canister/, https://minkj1992.github.io/icp_dao/
```

## refs
