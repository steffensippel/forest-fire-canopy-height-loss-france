# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 12:28:44 2026

@author: steff

extract the temperature and precipitation data from the copernicus website (get era5 modified data)
"""


#years = ["2015", "2016", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]

years = ["2022", "2023", "2024"]
import cdsapi
for year in years: 
    dataset = "derived-era5-single-levels-daily-statistics"
    request = {
        "product_type": "reanalysis",
        "variable": ["2m_temperature"],
        "year": year,
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

#%% extract the precipitation data: 
import cdsapi

year = "2018"
years = ["2024"]

for year in years: 
    dataset = "derived-era5-single-levels-daily-statistics"
    request = {
        "product_type": "reanalysis",
        "variable": ["total_precipitation"],
        "year": year,
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
        "daily_statistic": "daily_sum",
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "area": [52, -5, 40, 10]
    }
    
    client = cdsapi.Client()
    client.retrieve(dataset, request).download()
 
    
    
    
    
    
    
    
    
    
    
    
    