from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class MongoRepository(Generic[ModelT]):
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str, model: type[ModelT]) -> None:
        self.collection = db[collection_name]
        self.model = model

    async def create(self, data: dict[str, Any]) -> ModelT:
        now = datetime.now(UTC)
        data = self._serialize({**data, "created_at": now, "updated_at": now})
        result = await self.collection.insert_one(data)
        document = await self.collection.find_one({"_id": result.inserted_id})
        return self.model.model_validate(document)

    async def get(self, document_id: str) -> ModelT | None:
        if not ObjectId.is_valid(document_id):
            return None
        document = await self.collection.find_one({"_id": ObjectId(document_id)})
        return self.model.model_validate(document) if document else None

    async def find_one(self, query: dict[str, Any]) -> ModelT | None:
        document = await self.collection.find_one(query)
        return self.model.model_validate(document) if document else None

    async def list(self, query: dict[str, Any], limit: int = 100, skip: int = 0, sort: list[tuple[str, int]] | None = None) -> list[ModelT]:
        cursor = self.collection.find(query).skip(skip).limit(min(limit, 500))
        if sort:
            cursor = cursor.sort(sort)
        return [self.model.model_validate(document) async for document in cursor]

    async def update(self, document_id: str, data: dict[str, Any]) -> ModelT | None:
        if not ObjectId.is_valid(document_id):
            return None
        data = {k: v for k, v in data.items() if v is not None}
        data["updated_at"] = datetime.now(UTC)
        await self.collection.update_one({"_id": ObjectId(document_id)}, {"$set": self._serialize(data)})
        return await self.get(document_id)

    async def delete(self, document_id: str) -> bool:
        if not ObjectId.is_valid(document_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count == 1

    async def count(self, query: dict[str, Any]) -> int:
        return await self.collection.count_documents(query)

    def _serialize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._serialize(item) for key, item in value.items() if item is not None}
        if isinstance(value, list):
            return [self._serialize(item) for item in value]
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, BaseModel):
            return self._serialize(value.model_dump())
        if isinstance(value, (datetime, ObjectId, str, int, float, bool)) or value is None:
            return value
        return str(value)
