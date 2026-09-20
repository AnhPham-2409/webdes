from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class ItemCreate(BaseModel):
    name: str
    price: float

class ItemPublic(ItemCreate):
    id: int

_items: list[ItemPublic] = []
_next_id = 1

#find item or raise 404
def _find_item(item_id: int) -> ItemPublic:
    for item in _items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="item not found")


@app.get("/")
def home():
    return FileResponse("../frontend/items.html")


@app.get("/items/me")
def read_me():
    return "Welcome!"


# get all items
@app.get("/items", response_model=list[ItemPublic])
def list_items():
    return _items


# get one item
@app.get("/items/{item_id}", response_model=ItemPublic)
def get_item(item_id: int):
    return _find_item(item_id)


# create an item
@app.post("/items", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    global _next_id
    new_item = ItemPublic(id=_next_id, **item.model_dump())
    _items.append(new_item)
    _next_id += 1
    return new_item


# update an item
@app.put("/items/{item_id}", response_model=ItemPublic)
def update_item(item_id: int, updated: ItemCreate):
    existing = _find_item(item_id)
    existing.name = updated.name
    existing.price = updated.price
    return existing


# delete an item
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    item = _find_item(item_id)
    _items.remove(item)
    return None


app.mount("/static", StaticFiles(directory="../frontend"), name="static")