from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import date
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
import requests
import sys

# initially experimenting with just 2026 and only mcp
year1 = date.today().year
y = 0
while year1 > 2015:
    driver = webdriver.Firefox()
    driver.get("https://rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx")
    year = year1 - y
    id ="btn"+str(year) #year
    id1 = str(year)+"0" #all months
    try:
        WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, id)))
        driver.find_element(By.ID, id).click()
        WebDriverWait(driver,10).until(expected_conditions.element_to_be_clickable((By.ID, id1)))
        driver.find_element(By.ID, id1).click()
    except TimeoutException:
        print(f"WebPage Failed to Load {year} Properly")
        driver.quit()
        sys.exit()


    try:
        WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located((By.XPATH, "//a[img[contains(@alt, 'Monetary Policy Statement')]]")))
        pdf_imgs = driver.find_elements(By.XPATH, "//a[img[contains(@alt, 'Monetary Policy Statement')]]") #getting statement for a particular month
        WebDriverWait(driver,10).until(expected_conditions.presence_of_element_located(((By.XPATH, "//img[contains(@alt, 'Monetary Policy Statement')]"))))
        file_names = driver.find_elements(By.XPATH, "//img[contains(@alt, 'Monetary Policy Statement')]")#grabbing all pdf refs
        
    except TimeoutException:
        print(f"WebPage failed to locate/load the pdf properly")
        driver.quit()
        sys.exit()

    i = 0
    for file in file_names:
        file_names[i] = file.get_attribute("alt")#storing all file names
        i = i+1


    file_path, link, contents, i = [], [], [], 0

    for file in file_names:
        file_path.append("artifacts/"+file+".pdf")

    for img in pdf_imgs:
        url =  (img.get_attribute("href"))#grabbing href tag for url now need to use url to download the pdf
        link.append(url)
        contents.append(requests.get(url))#grabbing binary of the pdf
        

    for location in file_path:
        with open(location,"wb") as file:
            file.write(contents[i].content)# saving/writing binary of the pdf
        i = i+1
    print(link)
    driver.quit()
    y = y +1