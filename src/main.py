import logging
import time
import uuid

import structlog
import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uvicorn.protocols.utils import get_path_with_query_string

from app.api import crawl, greet, partners, reports, rooms
from app.logger import get_logger, init_logger
from chat import chat_server
from infra.config import get_config

app = FastAPI(title='Jarvis api server')
cfg = get_config()
init_logger(
    log_level=cfg.log_level(), 
    enable_json_logs=False
)
access_logger = get_logger("api.access")
error_logger = get_logger("api.error")

# Your CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/chat", chat_server)


routers = [
    greet.router,
    crawl.router,
    rooms.router,
    partners.router,
    reports.router
]
for router in routers:
    app.include_router(router)



@app.on_event("startup")
async def startup_event():
    await access_logger.info("Strating Jarvis server...")



@app.on_event("shutdown")
async def shutdown_event():
    await access_logger.info("Closing Jarvis server...")


@app.middleware("http")
async def logging_request_middleware(request: Request, call_next) -> Response:
    request_uuid_key = 'X-Request-ID'
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    request_id = request.headers.get(request_uuid_key)
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)    

    start_time = time.perf_counter_ns()
    

    try:
        response: Response = await call_next(request)
    except RequestValidationError as ex:
        exc_str = f'{ex}'.replace('\n', ' ').replace('   ', ' ')
        await error_logger.exception(f"{request}: {exc_str}")
        content = {'status_code': 10422, 'message': exc_str, 'data': None}
        response = JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        await error_logger.exception(f"Uncaught Exception")
        response = JSONResponse(content=repr(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # set X-Request-ID
        response.headers[request_uuid_key] = request_id
        process_time = time.perf_counter_ns() - start_time
        
        status_code = response.status_code
        url = get_path_with_query_string(request.scope)
        client_host = request.client.host
        client_port = request.client.port
        http_method = request.method
        http_version = request.scope["http_version"]
        # Recreate the Uvicorn access log format, but add all parameters as structured information
        await access_logger.info(
            f"""{client_host}:{client_port} - "{http_method} {url} HTTP/{http_version}" {status_code}""",
            http={
                "url": str(request.url),
                "status_code": status_code,
                "method": http_method,
                "request_id": request_id,
                "version": http_version,
            },
            network={"client": {"ip": client_host, "port": client_port}},
            duration=process_time,
        )
        response.headers["X-Process-Time"] = str(process_time / 10 ** 9)
        return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)


