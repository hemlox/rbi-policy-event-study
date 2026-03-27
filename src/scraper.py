from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.firefox.options import Options
from datetime import datetime
import requests
import sys
import os

def initialise_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)#headless selenium more efficient
    driver.get("https://rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx")
    os.makedirs("artifacts", exist_ok=True)
    return driver

def navigate_to_year(driver, year):
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

def extract_and_download(driver,year):
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
        date_obj = datetime.strptime(dates,"%b %d, %Y" )
        dates = date_obj.strftime("%d-%m-%Y")
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

def main():
    year = datetime.today().year
    while(year>2015):
        driver = initialise_driver()
        navigate_to_year(driver, year)
        extract_and_download(driver, year)
        year = year-1

if __name__ == "__main__":
    sys.exit(main())





