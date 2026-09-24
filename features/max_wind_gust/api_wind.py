# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 21:49:11 2026

@author: steff
"""

import cdsapi
import numpy as np 
import os 

os.environ["CDSAPI_URL"] = "https://cds.climate.copernicus.eu/api"

years = ["2017", "2018", "2019", "2020" ,"2021", "2022", "2023", "2024", "2025", "2026"]


            
dataset = "derived-era5-single-levels-daily-statistics"
request = {
    "product_type": "reanalysis",
    "variable": ["instantaneous_10m_wind_gust"],
    "year": ["2025"],
    "month": [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09",
        "10", "11", "12"
    ],
    "day": [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09",
        "10", "11", "12",
        "13", "14", "15",
        "16", "17", "18",
        "19", "20", "21",
        "22", "23", "24",
        "25", "26", "27",
        "28", "29", "30",
        "31"
    ],
    "daily_statistic": "daily_maximum",
    "time_zone": "utc+00:00",
    "frequency": "1_hourly",
    "area": [52, -5, 40, 10]
}

client = cdsapi.Client()
client.retrieve(dataset, request).download()
