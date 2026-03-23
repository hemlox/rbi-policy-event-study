from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import date
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.firefox.options import Options
import requests
import sys
import os
options = Options()
options.add_argument("--headless")
# initially experimenting with just 2026 and only mc
os.makedirs("artifacts", exist_ok=True)
year1 = date.today().year
year =year1
y = 0
while year > 2016:#extracting MCP statements 2016-present and gov statements 2021-present
    driver = webdriver.Firefox(options=options)#headless selenium more efficient
    driver.get("https://rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx")
    year = year1 - y
    id ="btn"+str(year) #year
    id1 = str(year)+"0" #all months
    #navigating to the page for that specific year-->architecture was changed in 2016
    if year!=2016:
        try:
            WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, id)))
            driver.find_element(By.ID, id).click()
            WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, id1)))
            driver.find_element(By.ID, id1).click()
        except TimeoutException:
            print(f"WebPage Failed to Load {year} Properly")
            driver.quit()
            sys.exit()
    else:
        try:
            WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, "divArchiveMain")))
            driver.find_element(By.ID, "divArchiveMain").click()
            WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, id)))
            driver.find_element(By.ID, id).click()
            WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, id1)))
            driver.find_element(By.ID, id1).click()
        except:
            print(f"WebPage Failed to Load {year} Properly")
            driver.quit()
            sys.exit()

    try:
        WebDriverWait(driver,10).until(expected_conditions.presence_of_all_elements_located((By.XPATH, "//a[img[(contains(@alt, 'Monetary Policy') and contains(@alt, 'Resolution')) or (contains(@alt, \"Governor’s Statement\"))]]")))
        #extracts MPC present-2016 and gov staterments from present-2021
        pdf_imgs = driver.find_elements(By.XPATH, "//a[img[(contains(@alt, 'Monetary Policy') and contains(@alt, 'Resolution')) or (contains(@alt, \"Governor’s Statement\"))]]")  #
        WebDriverWait(driver,10).until(expected_conditions.presence_of_all_elements_located(((By.XPATH, "//img[(contains(@alt, 'Monetary Policy') and contains(@alt, 'Resolution')) or (contains(@alt,\"Governor’s Statement\"))]"))))
        file_names = driver.find_elements(By.XPATH, "//img[(contains(@alt, 'Monetary Policy') and contains(@alt, 'Resolution')) or (contains(@alt,\"Governor’s Statement\"))]")
        file_names = [file.get_attribute("alt") for file in file_names]
        file_dates = [img.find_element(By.XPATH, "./preceding::h2[@class='dop_header'][1]").text for img in pdf_imgs]       
    except TimeoutException:
        print(f"WebPage failed to locate/load the pdf properly")
        driver.quit()
        sys.exit()
    
    link = []

    for file, dates, img in zip(file_names, file_dates, pdf_imgs):#storing all file paths using file name
        url =  (img.get_attribute("href"))#grabbing href tag for url now need to use url to download the pdf
        link.append(url)
        if "Governor’s" in file:
            path = "artifacts/"+"gov_statement_"+dates+".pdf"
            with open(path,"wb") as files:
                files.write(requests.get(url).content)#grabbing the binary of the pdf and saving it
        else:
            path = "artifacts/"+"mpc_resolution_"+dates+".pdf"
            with open(path,"wb") as files:
                files.write(requests.get(url).content)#grabbing the binary of the pdf and saving it
  
    print(f"{year}'s Links:", end=" ")
    print(link)
    driver.quit()
    y = y +1