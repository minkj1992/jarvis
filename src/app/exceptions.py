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


class FileEmptyContentsException(HTTPException):
    def __init__(
            self,
            file_name: str,
            headers: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Given file '{file_name}' does not contains any information.",
            headers=headers
        )


class InvalidFileExtException(HTTPException):
    def __init__(
            self,
            file_name: str,
            mime_type: str,
            headers: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"We cannot handle {mime_type} extension file, from '{file_name}'.",
            headers=headers
        )


class InvalidRoomInputTypeException(HTTPException):
    def __init__(
            self,
            input_type,
            headers: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid room input type {input_type}.",
            headers=headers
        )

class InvalidRelationTypeException(HTTPException):
    def __init__(
            self,
            input_type,
            headers: Optional[Dict[str, Any]] = None
        ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid relation type {input_type}.",
            headers=headers
        )



