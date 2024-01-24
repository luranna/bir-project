from fastapi import FastAPI, Form, Header, Request, status, Response, Depends, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel
import logon
import ssl
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import requests
import uvicorn

class SystemData(BaseModel):
    temperature: float
    battery: float


app = FastAPI()
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('./certs/server_cert.pem', keyfile='./certs/server_key.pem')

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.minTempValue = 20;
app.maxTempValue = 30;
app.currentTempValue=-99;
app.currentBatteryValue=-1;
app.minBatteryValue = 0;
app.maxBatteryValue = 1000;
app.systemMode="Off";


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def home(request: Request, access_token: str = Cookie(None)):
    if access_token is not None:
        data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
        return templates.TemplateResponse("main_page.html", {"request": request,"data": data})
    else:
        redirect_url = request.url_for('login') 
        return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND) 

@app.get("/login/", include_in_schema=False, response_class=HTMLResponse)
async def home(request: Request):
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
    return templates.TemplateResponse("logon_page.html", {"request": request,"data": data})

@app.post("/login/")
async def login(response: Response, request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    errors = []
    if not username:
        errors.append("Please Enter valid username")
    if not password:
        errors.append("Password enter password")
    if len(errors) > 0:
        return templates.TemplateResponse(
            "logon_page.html", {"request": request, "errors": errors}
        )
    try:
        usertemp =list(filter(lambda x:x["username"]==username,logon.users_data))
        user=usertemp[0]["username"]
        passw_db=usertemp[0]["hashed_password"]

        if user is None:
            errors.append("username does not exist")
            return templates.TemplateResponse(
                "logon_page.html", {"request": request, "errors": errors}
            )
        else:
            if logon.verify_password(password, passw_db):
                data = {"sub": username}
                jwt_token = jwt.encode(
                    data, logon.SECRET_KEY, algorithm=logon.ALGORITHM
                )
                msg = "Login Successful"
                response = RedirectResponse(url="/")
                response.set_cookie(
                    key="access_token", value=f"Bearer {jwt_token}", httponly=True
                )
                response.status_code = status.HTTP_303_SEE_OTHER
                return response
            else:
                errors.append("Invalid Password or Username")
                return templates.TemplateResponse(
                    "logon_page.html", {"request": request, "errors": errors}
                )
    except:
        errors.append("Something Wrong while authentication or storing tokens!")
        return templates.TemplateResponse(
            "logon_page.html", {"request": request, "errors": errors}
        )

@app.post("/update-data")
async def receive_data(request: Request, tempData: SystemData):
    app.currentTempValue=round(tempData.temperature,2)
    app.currentBatteryValue=tempData.battery
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
    return data

@app.get("/update-system-mode-on")
async def update_system_mode(request: Request):
    redirect_url = request.url_for('home')
    app.systemMode="On"
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/update-system-mode-off")
async def update_system_mode(request: Request):
    redirect_url = request.url_for('home')
    app.systemMode="Off"
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/update-system-mode-auto")
async def update_system_mode(request: Request):
    redirect_url = request.url_for('home')
    set_system_mode()
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "currentTempValue":app.currentTempValue, "currentBatteryValue":app.currentBatteryValue, "minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/temperature_parameters")
async def get_temp_limits(request: Request):
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue} 
    return data

@app.get("/battery_parameters")
async def get_battery_limits(request: Request):
    data={"minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue} 
    return data

@app.get("/system-mode")
async def get_system_mode(request: Request):
    if("On" in app.systemMode):
        data={"systemMode": "On"}
    else:
        data={"systemMode": "Off"}
    return data

@app.post("/update-temp-limits")
async def update_temp_limits(request: Request, minTemp= Form(None), maxTemp=Form(None)):
    redirect_url = request.url_for('home')
    if (minTemp is None or not is_number(minTemp)) and (maxTemp  is None or not is_number(maxTemp)):
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
    set_system_mode()
    data={"minTempValue": app.minTempValue,  "maxTempValue":app.maxTempValue, "systemMode":app.systemMode} 
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/update-battery-limits")
async def update_battery_limits(request: Request, minBattery = Form(None), maxBattery=Form(None)):
    redirect_url = request.url_for('home')
    if (minBattery is None or not is_number(minBattery)) and (maxBattery  is None or not is_number(maxBattery)):
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    if minBattery is None or not is_number(minBattery):
        minBattery=app.minBatteryValue
        if float(maxBattery) < float(app.minBatteryValue):
            app.maxBatteryValue = app.minBatteryValue
            app.minBatteryValue = maxBattery
            return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
    if maxBattery is None or not is_number(maxBattery):
        if float(minBattery) > float(app.maxBatteryValue):
            app.minBatteryValue = app.maxBatteryValue
            app.maxBatteryValue = minBattery
            return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER) 
        maxBattery=app.maxBatteryValue   
    minBattery=float(minBattery)
    maxBattery=float(maxBattery)
    app.minBatteryValue=round(minBattery,2)
    app.maxBatteryValue=round(maxBattery,2)
    if app.minBatteryValue > app.maxBatteryValue:
        app.minBatteryValue , app.maxBatteryValue = app.maxBatteryValue, app.minBatteryValue 
    set_system_mode()
    data={"minBatteryValue": app.minBatteryValue,  "maxBatteryValue":app.maxBatteryValue, "systemMode":app.systemMode} 
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

def set_system_mode():
    if((app.currentTempValue < app.maxTempValue) and (app.currentTempValue > app.minTempValue) and (app.currentBatteryValue <app.maxBatteryValue) and (app.currentBatteryValue > app.minBatteryValue)):
       app.systemMode="Automatic (On)"
    else:
        app.systemMode="Automatic (Off)"

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True

@app.get("/test_cookie/")
async def read_cookie(access_token: str = Cookie(None)):
   return {"access_token": access_token}

@app.get("/logout/")
def logout(response : Response):
 response.delete_cookie("access_token")
 response = RedirectResponse(url="/login/")
 return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, ssl_certfile="./certs/server_cert.pem", ssl_keyfile="./certs/server_key.pem")
