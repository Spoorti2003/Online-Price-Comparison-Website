import streamlit as st
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz, process
import pandas as pd
import re

# Function to fetch data from Amazon
def fetch_amazon_data(product_name):
    url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        products = []
        product_divs = soup.find_all("div", {"data-component-type": "s-search-result"})
        for product in product_divs:
            try:
                title = product.h2.text.strip()
                price = product.find("span", "a-price-whole").text.strip() if product.find("span", "a-price-whole") else "Price not available"
                image = product.find("img")['src']
                link = "https://www.amazon.in" + product.h2.a['href']
                rating = product.find("span", {"class": "a-icon-alt"}).text.strip() if product.find("span", {"class": "a-icon-alt"}) else "No rating"
                products.append({"title": title, "price": price, "image": image, "link": link, "rating": rating})
            except Exception as e:
                st.warning(f"Error processing Amazon product: {e}")
    except Exception as e:
        st.error(f"Error fetching Amazon data: {e}")
    
    return products

# Function to fetch data from Snapdeal
def fetch_snapdeal_data(product_name):
    url = f"https://www.snapdeal.com/search?keyword={product_name.replace(' ', '%20')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        products = []
        product_divs = soup.find_all("div", {"class": "product-tuple-listing"})

        for product in product_divs:
            try:
                title_tag = product.find("p", {"class": "product-title"})
                price_tag = product.find("span", {"class": "lfloat product-price"})
                image_tag = product.find("img", {"class": "product-image"})
                link_tag = product.find("a", {"class": "dp-widget-link"})

                if title_tag and price_tag and image_tag and link_tag:
                    title = title_tag.text.strip()
                    price = price_tag.text.strip()
                    image = image_tag['src'] if 'src' in image_tag.attrs else None
                    link = link_tag['href']
                    products.append({"title": title, "price": price, "image": image, "link": link})
                else:
                    st.warning("Some product details are missing. Skipping this product.")
            except Exception as e:
                st.warning(f"Error processing Snapdeal product: {e}")
    except Exception as e:
        st.error(f"Error fetching Snapdeal data: {e}")
    
    return products

# Function to normalize product titles
def normalize_title(title):
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    return title.strip()

# Function to find common products between Snapdeal and Amazon using fuzzy matching
def find_common_products(amazon_products, snapdeal_products):
    amazon_titles = {normalize_title(product['title']): product for product in amazon_products}
    snapdeal_titles = [normalize_title(product['title']) for product in snapdeal_products]

    common_products = []
    for snapdeal_title in snapdeal_titles:
        best_match, score = process.extractOne(snapdeal_title, amazon_titles.keys(), scorer=fuzz.token_set_ratio)
        
        if score > 50:  # Adjust the threshold as needed
            common_product = amazon_titles[best_match]
            snapdeal_product = next(p for p in snapdeal_products if normalize_title(p['title']) == snapdeal_title)
            common_products.append({
                "amazon": common_product,
                "snapdeal": snapdeal_product
            })

    return common_products

# Streamlit App
st.title("Compare Product Prices")
st.markdown("Enter the product name to find common products between Amazon and Snapdeal.")

# User input
product_name = st.text_input("Enter the product name")

if st.button("Compare Prices"):
    if product_name:
        with st.spinner("Fetching data..."):
            amazon_products = fetch_amazon_data(product_name)
            snapdeal_products = fetch_snapdeal_data(product_name)

            common_products = find_common_products(amazon_products, snapdeal_products)

        # Displaying Amazon products
        st.subheader("Amazon Products")
        if amazon_products:
            for product in amazon_products:
                st.image(product['image'], width=150)
                st.markdown(f"[{product['title']}]({product['link']})")
                st.write(f"Price: ₹{product['price']}")
                st.write(f"Rating: {product['rating']}")
        else:
            st.write("No products found on Amazon.")

        # Displaying Snapdeal products
        st.subheader("Snapdeal Products")
        if snapdeal_products:
            for product in snapdeal_products:
                if product['image']:
                    st.image(product['image'], width=150)
                else:
                    st.write("No image available")
                st.markdown(f"[{product['title']}]({product['link']})")
                st.write(f"Price: ₹{product['price']}")
        else:
            st.write("No products found on Snapdeal.")

        # Display common products
        if common_products:
            st.write("### Common Products")
            for products in common_products:
                amazon_product = products['amazon']
                snapdeal_product = products['snapdeal']
                
                # Create two columns for better layout
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Amazon**")
                    st.image(amazon_product['image'], width=150)
                    st.markdown(f"[{amazon_product['title']}]({amazon_product['link']})")
                    st.write(f"Price: ₹{amazon_product['price']}")
                    st.write(f"Rating: {amazon_product['rating']}")
                
                with col2:
                    st.write("**Snapdeal**")
                    if snapdeal_product['image']:
                        st.image(snapdeal_product['image'], width=150)
                    else:
                        st.write("No image available")
                    st.markdown(f"[{snapdeal_product['title']}]({snapdeal_product['link']})")
                    st.write(f"Price: ₹{snapdeal_product['price']}")
        else:
            st.write("No common products found between Amazon and Snapdeal.")
    else:
        st.write("Please enter a product name.")

