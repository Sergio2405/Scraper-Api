from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from requests import Session
from bs4 import BeautifulSoup 
import pandas as pd 
import re 

URL = "https://www.sbs.gob.pe/app/pu/ccid/paginas/vp_rentafija.aspx" 
re_ = "^(0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012])[- /.](19|20)\d\d$" 

app = FastAPI()
templates = Jinja2Templates(directory="templates")

excel_path = "reporte.xlsx"

@app.get("/")
def verify():
    return "Connection working"

@app.get("/main")
def main(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.post("/generate")
def generate(dates:List[str]):
    with Session() as req:
        r = req.get(URL) 
        soup = BeautifulSoup(r.content, 'html.parser') 
        #times = [item.get("value") for item in soup.findAll( "option",value=re.compile(re_))]

        vs = soup.find("input", id="__VIEWSTATE").get("value")
        vsg = soup.find("input", id="__VIEWSTATEGENERATOR").get("value")
        ev_val = soup.find("input", id="__EVENTVALIDATION").get("value")

        writer = pd.ExcelWriter('reporte.xlsx', engine='xlsxwriter')

        for time in dates:
            data = {
                    '__VIEWSTATE': vs,
                    '__VIEWSTATEGENERATOR': vsg,
                    '__EVENTVALIDATION':ev_val,
                    'cboFecProceso':time, 
                    'btnConsultar':"Consultar"
                }
            r = req.post(URL, data=data)
            soup = BeautifulSoup(r.content, 'html.parser') 
            report = soup.find("table",id="tablaReporte").find("tbody")
            
            table = []
            for tr in report.find_all("tr"):
                temp_tr=[]
                tds = tr.find_all("td")
                for i in [1,2,3,4,5,9]:
                    temp_tr.append(tds[i].string)
                table.append(temp_tr)
            df = pd.DataFrame(table)
            df.to_excel(writer, sheet_name=time.replace("/","|"),index=False)
        writer.save()
    print("Saving Excel")
    return "Report generated" 

@app.get("/obtain")
def obtain():
    return FileResponse(excel_path)
