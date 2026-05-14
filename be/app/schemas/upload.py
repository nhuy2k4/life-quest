from pydantic import BaseModel


class UploadResponse(BaseModel):
    url: str
    public_id: str
