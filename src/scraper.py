from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import date
import requests

# initially experimenting with just 2026 and only mcp
driver = webdriver.Firefox()
driver.get("https://rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx")
year = date.today().year
id ="btn"+str(year) #year
id1 = str(year)+"0" #all months
driver.find_element(By.ID, id).click()
driver.find_element(By.ID, id1).click()
pdf_img = driver.find_element(By.XPATH, "//a[img[contains(@alt, 'Monetary Policy Statement')]]") #getting statement for a particular month
file_name = driver.find_element(By.XPATH, "//img[contains(@alt, 'Monetary Policy Statement')]").get_attribute("alt")#grabbing complete alt for file name
driver.close()
file_path = "artifacts/"+file_name+".pdf"
link = pdf_img.get_attribute("href")#grabbing href tag for url now need to use url to download the pdf
contents = requests.get(link)#grabbing binary of the pdf
with open(file_path,"wb") as file:
    file.write(contents.content)# saving/writing binary of the pdf
print(link)
