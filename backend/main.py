import logging
import time

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response, statusfrom fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

# ---------- logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")



# ---------- app ----------
app = FastAPI()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(body: LoginRequest, response: Response):
    # demo only: replace with a real user lookup and password hash check
    if body.username != "admin" or body.password != "123456":
        raise HTTPException(status_code=401, detail="invalid username or password")
    response.set_cookie("session", "fake-session-token", httponly=True, samesite="lax")
    return {"message": "login ok"}
# app.mount("/static", StaticFiles(directory="../frontend"), name="static")


# ---------- middleware ----------
# the first one registered is the innermost, the last one is the outermost

# log method, path and processing time for every request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s %.2f ms", request.method, request.url.path, elapsed_ms)
    return response



# added last, so it is the outermost layer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],  # your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# outermost: cors, so even 500 responses get cors headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ui.example.com"],  # replace with your frontend's real origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- dependencies ----------
def pagination(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "secret-api-key":
        raise HTTPException(status_code=401, detail="invalid api key")
    return x_api_key


# ---------- routers ----------
admin = APIRouter(prefix="/admin", dependencies=[Depends(verify_api_key)])


# ---------- models ----------
class ItemCreate(BaseModel):
    name: str
    price: float


class ItemPublic(ItemCreate):
    id: int


# ---------- in-memory storage ----------
_items: list[ItemPublic] = []
_next_id = 1
_cart: list[str] = []


# find item or raise 404
def _find_item(item_id: int) -> ItemPublic:
    for item in _items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="item not found")


# ---------- routes: general ----------
@app.get("/")
def home():
    return FileResponse("../frontend/items.html")


@app.get("/boom")
def boom():
    x = 10 / 0
    return {"result": x}


# ---------- routes: items ----------
# note: /items/me must be declared before /items/{item_id}
@app.get("/items/me")
def read_me():
    return "welcome!"


@app.get("/items/{item_id}", response_model=ItemPublic)
def get_item(item_id: int):
    return _find_item(item_id)


@app.post("/items", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    global _next_id
    new_item = ItemPublic(id=_next_id, **item.model_dump())
    _items.append(new_item)
    _next_id += 1
    return new_item


@app.put("/items/{item_id}", response_model=ItemPublic)
def update_item(item_id: int, updated: ItemCreate):
    existing = _find_item(item_id)
    existing.name = updated.name
    existing.price = updated.price
    return existing


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    item = _find_item(item_id)
    _items.remove(item)
    return None


# ---------- routes: admin ----------
@admin.get("/items", response_model=list[ItemPublic])
def list_items(page: dict = Depends(pagination)):
    skip = page["skip"]
    limit = page["limit"]
    return _items[skip : skip + limit]


# ---------- routes: cart ----------
@app.post("/cart/add")
def add_cart_item(item: str):
    _cart.append(item)
    return item


@app.get("/cart")
def get_cart():
    return _cart


# ---------- include routers ----------
app.include_router(admin)