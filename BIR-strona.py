#start serwera komenda (wpisywane w terminalu)-> uvicorn BIR-strona:app --reload
from typing import Union

from fastapi import FastAPI, Form, Request, status
from pydantic import BaseModel
from typing_extensions import Annotated
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

class SystemData(BaseModel):
    temperature: float


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.minTempValue = 20;
app.maxTempValue = 30;
app.currentTempValue=23;


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def home(request: Request):
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue} 
    return templates.TemplateResponse("main_page.html", {"request": request,"data": data})


@app.post("/temperature/")
async def receive_temperature(request: Request, tempData: SystemData):
    app.currentTempValue=tempData.temperature
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue} 
    return data

@app.get("/parameters/")
async def get_temp_limits(request: Request):
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue} 
    return data

@app.post("/update-temp-limits/")
async def update_temp_limits(request: Request, minTemp: str = Form(None), maxTemp=Form(None)):
    redirect_url = request.url_for('home') 
    if minTemp is None or not is_number(minTemp):
        minTemp=app.minTempValue
        if float(maxTemp) < float(app.minTempValue):
            app.maxTempValue = app.minTempValue
            app.minTempValue = maxTemp
            return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
    if maxTemp is None or not is_number(maxTemp):
        if float(minTemp) > float(app.maxTempValue):
            app.minTempValue = app.maxTempValue
            app.maxTempValue = minTemp
            return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
        maxTemp=app.maxTempValue   
    minTemp=float(minTemp)
    maxTemp=float(maxTemp)
    app.minTempValue=round(minTemp,2)
    app.maxTempValue=round(maxTemp,2)
    if app.minTempValue > app.maxTempValue:
        app.minTempValue , app.maxTempValue = app.maxTempValue, app.minTempValue 
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue} 
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True

#testowe requesty:curl -X 'POST' \
#  'http://127.0.0.1:8000/update-data' \
#  -H 'accept: application/json' \
##  -H 'Content-Type: application/json' \
# -d '{
#  "name": "Maszyna",
#  "temperature": 32
#}'
