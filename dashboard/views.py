# from django.shortcuts import render
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
from .utils import fetch_prices
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages




# from django.contrib.auth.decorators import login_required





# @login_required
def dashboard_view(request):
    data_preview = None
    graphs = {}

    if request.method == "POST":
        flipkart_url = request.POST.get("flipkart_url")
        num_pages = int(request.POST.get("num_pages", 1))  # Get the number of pages from the form, default to 1

        # Initialize Selenium WebDriver
        driver = webdriver.Chrome()  # Ensure chromedriver is installed and set up
        reviews = []
        ratings = []
        locations = []

        # Loop through the pages and extract review data
        for page in range(1, num_pages + 1):
            page_url = f"{flipkart_url}?page={page}"  # Update this based on how the pagination works on the website
            driver.get(page_url)
            time.sleep(5)  # Adjust the delay as needed

            # Parse page source
            content = driver.page_source
            soup = BeautifulSoup(content, "lxml")

            # Scrape review data
            review_containers = soup.find_all("div", class_="col EPCmJX Ma1fCG")
            for container in review_containers:
                review_text = container.find("div", class_="ZmyHeo")
                reviews.append(review_text.get_text(strip=True) if review_text else "N/A")

                rating = container.find("div", class_="XQDdHH Ga3i8K")
                ratings.append(rating.get_text(strip=True) if rating else "N/A")

                location = container.find("p", class_="MztJPv")
                locations.append(location.get_text(strip=True) if location else "N/A")

        driver.quit()  # Close the driver

        # Create a DataFrame
        df = pd.DataFrame({
            "Review Text": reviews,
            "Rating": ratings,
            "Location": locations
        })

        # Save DataFrame to CSV
        csv_path = "dashboard/static/preprocessed_data.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")

        # Generate graphs
        graphs = create_graphs(df)

        # Perform sentiment analysis
        sentiment_report = perform_sentiment_analysis(df)

        # Preview data in the template
        data_preview = df.head().to_html(classes="table table-striped", index=False)

        return render(request, "dashboard.html", {
            "data": data_preview,
            "graphs": graphs,
            "sentiment_report": sentiment_report,
        })

    return render(request, "dashboard.html", {"data": data_preview})


def create_graphs(df):
    graph_paths = {}

    # Clean and convert the Rating column
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

    # Distribution of Ratings
    plt.figure(figsize=(8, 6))
    df["Rating"].dropna().value_counts().sort_index().plot(kind="bar", color="skyblue")
    plt.title("Distribution of Ratings")
    plt.xlabel("Rating")
    plt.ylabel("Count")
    rating_graph = "dashboard/static/ratings_distribution.png"
    plt.savefig(rating_graph)
    plt.close()
    graph_paths["ratings"] = rating_graph

    # Word Cloud for Reviews
    reviews = " ".join(df["Review Text"])
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(reviews)
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    wordcloud_path = "dashboard/static/wordcloud.png"
    plt.savefig(wordcloud_path)
    plt.close()
    graph_paths["wordcloud"] = wordcloud_path

    # Average Rating by Location
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

    # Sentiment Analysis Distribution
    sentiments = perform_sentiment_analysis(df)["labels"]
    sentiment_counts = pd.Series(sentiments).value_counts()
    plt.figure(figsize=(8, 6))
    sentiment_counts.plot(kind="bar", color=["green", "red", "blue"])
    plt.title("Sentiment Distribution")
    plt.xlabel("Sentiment")
    plt.ylabel("Count")
    sentiment_graph = "dashboard/static/sentiment_distribution.png"
    plt.savefig(sentiment_graph)
    plt.close()
    graph_paths["sentiment"] = sentiment_graph

    # Negative Reviews Analysis
    negative_reviews = df[perform_sentiment_analysis(df)["labels"] == "Negative"]
    if not negative_reviews.empty:
        # Word Cloud for Negative Reviews
        negative_reviews_text = " ".join(negative_reviews["Review Text"])
        negative_wordcloud = WordCloud(
            width=800, height=400, background_color="white"
        ).generate(negative_reviews_text)
        plt.figure(figsize=(10, 6))
        plt.imshow(negative_wordcloud, interpolation="bilinear")
        plt.axis("off")
        negative_wordcloud_path = "dashboard/static/negative_wordcloud.png"
        plt.savefig(negative_wordcloud_path)
        plt.close()
        graph_paths["negative_wordcloud"] = negative_wordcloud_path

        # Top Negative Keywords
        vectorizer = CountVectorizer(stop_words="english")
        X = vectorizer.fit_transform(negative_reviews["Review Text"])
        words = vectorizer.get_feature_names_out()
        sum_words = X.sum(axis=0)
        word_freq = [(word, sum_words[0, idx]) for word, idx in zip(words, range(len(words)))]
        word_freq = sorted(word_freq, key=lambda x: x[1], reverse=True)[:10]
        
        plt.figure(figsize=(10, 6))
        plt.bar([w[0] for w in word_freq], [w[1] for w in word_freq], color="red")
        plt.title("Top Keywords in Negative Reviews")
        plt.xlabel("Keywords")
        plt.ylabel("Frequency")
        negative_keywords_path = "dashboard/static/negative_keywords.png"
        plt.savefig(negative_keywords_path)
        plt.close()
        graph_paths["negative_keywords"] = negative_keywords_path

    return graph_paths


def perform_sentiment_analysis(df):
    reviews = df["Review Text"].tolist()

    def preprocess_data(reviews):
        labels = []
        processed_reviews = []
        for review in reviews:
            if "good" in review.lower() or "excellent" in review.lower():
                labels.append("Positive")
            elif "bad" in review.lower() or "poor" in review.lower() or "worst" in review.lower():
                labels.append("Negative")
            else:
                labels.append("Neutral")

            processed_reviews.append(review.lower())
        return processed_reviews, labels

    processed_reviews, labels = preprocess_data(reviews)

    # Train Sentiment Classifier
    X_train, X_test, y_train, y_test = train_test_split(
        processed_reviews, labels, test_size=0.2, random_state=42
    )

    # Convert text data into feature vectors using CountVectorizer
    vectorizer = CountVectorizer()
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Train a Naive Bayes classifier
    classifier = MultinomialNB()
    classifier.fit(X_train_vec, y_train)

    # Return labels for distribution
    return {"labels": labels}

# from django.shortcuts import render
# from django.http import HttpResponse
# from .utils import fetch_prices  # Custom utility function to scrape prices

def compare_prices_view(request):
    prices = None
    product_name = None

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        if product_name:
            prices = fetch_prices(product_name)  # Fetch prices for the given product

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


# Registration View
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

# Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('/')  # Redirect to the dashboard or home page
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')
