from selenium import webdriver
from bs4 import BeautifulSoup

def fetch_prices(product_name):
    urls = {
        "Flipkart": f"https://www.flipkart.com/search?q={product_name}",
        "Amazon": f"https://www.amazon.in/s?k={product_name}",
    }

    prices = {}
    driver = webdriver.Chrome()

    for site, url in urls.items():
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        if site == "Amazon":
            price_element = soup.find("span", class_="a-price-whole")
        elif site == "Flipkart":
            price_element = soup.find("div", class_="Nx9bqj _4b5DiR")

        price = price_element.get_text(strip=True) if price_element else "N/A"
        prices[site] = price

    driver.quit()
    return prices
