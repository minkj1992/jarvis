from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class RoomNotFoundException(HTTPException):
    def __init__(
            self,
            room_pk: str,
            headers: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room not found for {room_pk}",
            headers=headers
        )

class RoomChainNotFoundException(HTTPException):
    def __init__(
            self,
            room_pk: str,
            headers: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room chain not found for {room_pk}",
            headers=headers
        )
