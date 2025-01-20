from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import os
import time
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .utils import fetch_prices

def dashboard_view(request):
    data_preview = None
    graphs = {}

    if request.method == "POST":
        flipkart_url = request.POST.get("flipkart_url")
        num_pages = int(request.POST.get("num_pages", 1))

        driver = webdriver.Chrome()  # Ensure chromedriver is installed and set up
        reviews, ratings, locations = [], [], []

        try:
            for page in range(1, num_pages + 1):
                page_url = f"{flipkart_url}?page={page}"
                driver.get(page_url)
                time.sleep(5)  # Adjust the delay as needed

                content = driver.page_source
                soup = BeautifulSoup(content, "lxml")

                review_containers = soup.find_all("div", class_="col EPCmJX Ma1fCG")
                for container in review_containers:
                    review_text = container.find("div", class_="ZmyHeo")
                    reviews.append(review_text.get_text(strip=True) if review_text else "N/A")

                    rating = container.find("div", class_="XQDdHH Ga3i8K")
                    ratings.append(rating.get_text(strip=True) if rating else "N/A")

                    location = container.find("p", class_="MztJPv")
                    locations.append(location.get_text(strip=True) if location else "N/A")
        except Exception as e:
            print("Error during scraping:", e)
        finally:
            driver.quit()

        if len(ratings) != len(reviews):
            print("Mismatch between reviews and ratings lengths")
        
        df = pd.DataFrame({
            "Review Text": reviews,
            "Rating": ratings if len(ratings) == len(reviews) else [None] * len(reviews),
            "Location": locations if len(locations) == len(reviews) else [None] * len(reviews),
        })

        csv_path = "dashboard/static/preprocessed_data.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")

        graphs = create_graphs(df)
        sentiment_report = perform_sentiment_analysis(df)
        data_preview = df.head().to_html(classes="table table-striped", index=False)

        return render(request, "dashboard.html", {
            "data": data_preview,
            "graphs": graphs,
            "sentiment_report": sentiment_report,
        })

    return render(request, "dashboard.html", {"data": data_preview})

def create_graphs(df):
    graph_paths = {}

    if "Rating" in df.columns:
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

        plt.figure(figsize=(8, 6))
        df["Rating"].dropna().value_counts().sort_index().plot(kind="bar", color="skyblue")
        plt.title("Distribution of Ratings")
        plt.xlabel("Rating")
        plt.ylabel("Count")
        rating_graph = "dashboard/static/ratings_distribution.png"
        plt.savefig(rating_graph)
        plt.close()
        graph_paths["ratings"] = rating_graph

    reviews = " ".join(df["Review Text"])
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(reviews)
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    wordcloud_path = "dashboard/static/wordcloud.png"
    plt.savefig(wordcloud_path)
    plt.close()
    graph_paths["wordcloud"] = wordcloud_path

    if "Location" in df.columns and "Rating" in df.columns:
        avg_rating_by_location = (
            df.groupby("Location")["Rating"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
        )
        plt.figure(figsize=(10, 6))
        avg_rating_by_location.plot(kind="bar", color="green")
        plt.title("Top 10 Locations by Average Rating")
        plt.xlabel("Location")
        plt.ylabel("Average Rating")
        plt.xticks(rotation=45)
        avg_rating_path = "dashboard/static/avg_rating_by_location.png"
        plt.savefig(avg_rating_path)
        plt.close()
        graph_paths["avg_rating"] = avg_rating_path

    return graph_paths

def perform_sentiment_analysis(df):
    reviews = df["Review Text"].tolist()

    def preprocess_data(reviews):
        labels = []
        for review in reviews:
            if "good" in review.lower() or "excellent" in review.lower():
                labels.append("Positive")
            elif "bad" in review.lower() or "poor" in review.lower():
                labels.append("Negative")
            else:
                labels.append("Neutral")
        return labels

    labels = preprocess_data(reviews)
    return {"labels": labels}

def compare_prices_view(request):
    prices = None
    product_name = None

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        if product_name:
            prices = fetch_prices(product_name)

    return render(request, "compare_prices.html", {"product_name": product_name, "prices": prices})

def download_csv_view(request):
    file_path = "dashboard/static/preprocessed_data.csv"
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            response = HttpResponse(f, content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="reviews.csv"'
            return response
    return HttpResponse("File not found", status=404)

def download_image_view(request, filename):
    file_path = os.path.join("dashboard/static", filename)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return FileResponse(f, content_type="image/png")
    return HttpResponse("File not found", status=404)

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, "Registration successful. Please log in.")
                return redirect('login')
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('/')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')
