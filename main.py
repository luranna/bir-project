from typing import Union

from fastapi import FastAPI, Form, Request, status
from pydantic import BaseModel
from typing_extensions import Annotated
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import ssl

import uvicorn

class SystemData(BaseModel):
    temperature: float
    battery: int


app = FastAPI()
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('./certs/server_cert.pem', keyfile='./certs/server_key.pem')

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.minTempValue = 20;
app.maxTempValue = 30;
app.currentTempValue=23;
app.currentBatteryValue=100;
app.minBatteryValue = 0;
app.maxBatteryValue = 1000;


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def home(request: Request):
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue} 
    return templates.TemplateResponse("main_page.html", {"request": request,"data": data})


@app.post("/update-data")
async def receive_data(request: Request, tempData: SystemData):
    app.currentTempValue=round(tempData.temperature,2)
    app.currentBatteryValue=tempData.battery
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue} 
    return data

@app.get("/temperature_parameters")
async def get_temp_limits(request: Request):
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue} 
    return data

@app.get("/battery_parameters")
async def get_battery_limits(request: Request):
    data={"minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue} 
    return data

@app.post("/update-temp-limits")
async def update_temp_limits(request: Request, minTemp: str = Form(None), maxTemp=Form(None)):
    redirect_url = request.url_for('home')
    if (minTemp is None or not is_number(minTemp)) and (maxTemp  is None or is_number(maxTemp)):
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
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

@app.post("/update-battery-limits")
async def update_battery_limits(request: Request, minBattery: str = Form(None), maxBattery=Form(None)):
    redirect_url = request.url_for('home') 
    if (minBattery is None or not is_number(minBattery)) and (maxBattery  is None or not is_number(maxBattery)):
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
    if minBattery is None or not is_number(minBattery):
        minBattery=app.minBatteryValue
        if maxBattery < app.minBatteryValue:
            app.maxBatteryValue = app.minBatteryValue
            app.minBatteryValue = maxBattery
            return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
    if maxBattery is None or not is_number(maxBattery):
        if minBattery > app.maxBatteryValue:
            app.minBatteryValue = app.maxBatteryValue
            app.maxBatteryValue = minBattery
            return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
        maxBattery=app.maxBatteryValue
    app.minBatteryValue=minBattery
    app.maxBatteryValue=maxBattery
    print(app.minBatteryValue)
    print(app.maxBatteryValue)
    if app.minBatteryValue > app.maxBatteryValue:
        app.minBatteryValue , app.maxBatteryValue = app.maxBatteryValue, app.minBatteryValue 
    data={"minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue} 
    print(app.minBatteryValue)
    print(app.maxBatteryValue)
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080, ssl_keyfile="./certs/server_key.pem", ssl_certfile="./certs/server_cert.pem")
