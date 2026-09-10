from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

def predict_price(area: float, bedrooms: int, location: str) -> float:
    base_price = 500
    price = base_price + (15 * area) + (50 * bedrooms)
    
    if location == "hanoi":
        price = price * 1.3
    elif location == "hcmc":
        price = price * 1.25
    else:
        price = price
        
    return round(price)

@app.get("/predict")
def get_prediction(area: float, bedrooms: int, location: str = "other"):
    prediction = predict_price(area, bedrooms, location)
    return {
        "area": area, 
        "bedrooms": bedrooms, 
        "location": location, 
        "predict_price": prediction
    }

app.mount(
    "/static",
    StaticFiles(directory="../frontend"),
    name="static"
)

@app.get("/")
def home():
    return FileResponse("../frontend/house_form.html")