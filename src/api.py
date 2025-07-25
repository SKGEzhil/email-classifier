from fastapi import FastAPI
from pydantic import BaseModel

import sys

print(sys.executable)  # path to the Python interpreter
print(sys.version)     # full version string

# import inference
from . import inference

print("MODEL_LOADED", flush=True)
app = FastAPI()

class Message(BaseModel):
    text: str

label = {
    0: "Academics",
    1: "Clubs",
    2: "Internships",
    3: "Others",
    4: "Seminars",
}

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI"}

@app.post("/predict")
async def predict(message: Message):
    # Here you would call your prediction function
    # For demonstration, we return a dummy response
    prediction = inference.predict(message.text)
    return {"prediction": label[prediction], "id": prediction}
