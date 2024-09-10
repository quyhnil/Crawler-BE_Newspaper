from pydantic import BaseModel

class NewspaperItemBase(BaseModel):
    source: str
    link: str
    title: str
    time: str
    tags: str
    content: str

class NewspaperItem(NewspaperItemBase):
    id: int
    
    class Config:
        from_attributes = True