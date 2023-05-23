from fastapi import WebSocket


async def wss_close_ignore_exception(websocket: WebSocket):
    try:
        await websocket.close()        
    except Exception:
        pass


