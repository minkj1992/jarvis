# dev step


## model
> just with redis and docker-compose on ec2


- [openai's vector_database](https://github.com/openai/openai-cookbook/blob/main/examples/vector_databases/Using_vector_databases_for_embeddings_search.ipynb)
- [openai's redis example](https://github.com/openai/openai-cookbook/blob/main/examples/vector_databases/redis/getting-started-with-redis-and-openai.ipynb)
- [LangChain Redis docs](https://python.langchain.com/en/latest/modules/indexes/vectorstores/examples/redis.html)


`Partners`
uuid
oauth:enum
plan:enum (z, a,b,c,d) default(z)
credit:int default(0)
access_token: str
refresh_token: str
is_active: bool help(탈퇴여부)

`Apikey`
partner_uuid: pk
api_key: str

`Room`
uuid
partner_uuid
question_template: str
vector_storage : HASH data type

## 1. Without server

- [ ] Get a uri and crawling pages from sitemap
- [ ] Create vector embeddings of sitemap contents
- [ ] Chat with designed template


## 2. With Server

- [ ] Generate local docker-compose
    - redis for total database
    - fastapi
- [ ] Build web server api
    - [notion docs](https://minkj1992.notion.site/SiteGPT-db69971686ed4017a76c0db8a40cc52d)


## Flow

### 1. 사용자가 채팅방을 만드는 플로우

1. website uri를 넣는다.
2. 크롤러가 동작하여, 웹사이트를 긁어 모은다.
3. 크롤러가 학습한다.
4. 완료되면 학습한 데이터를 vector store로 redis hash에 넣어 room을 만든다.

### 2. 사용자가 채팅하는 플로우

1. /rooms에서 room_uuid을 선택한다.
2. room_uuid를 통해 질문한다.
3. redis hash에서 room_uuid를 통해 vector store를 가져온다.
4. 질문에 대해서 template를 통해 chatgpt에게 물어본다.
5. 받은 답을 bubble로 보낸다.

## Design
- [fastapi websocket](https://medium.com/@ahtishamshafi9906/how-to-build-a-simple-chat-application-in-fastapi-7bafad755654)

### `/learn`
> crawl with sitemap


- **POST /learn**

```
{
    uri
    auth
}
```

return site_uris


### `/rooms`

- **GET /rooms**
- **POST /rooms**
    1. crawl site
    2. generate model
    3. return room uuid




