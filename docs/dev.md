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