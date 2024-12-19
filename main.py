from flask import Flask, render_template, request, redirect, url_for
import matplotlib.pyplot as plt
import os
from io import BytesIO
import base64
import pandas as pd
from textblob import TextBlob
from collections import Counter
import re

# Initialize Flask app
app = Flask(__name__)

# Helper function for sentiment analysis
def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "Positive"
    elif analysis.sentiment.polarity == 0:
        return "Neutral"
    else:
        return "Negative"

# Helper function for extracting most common words
def get_most_common_words(tweets, num_words=10):
    all_words = ' '.join(tweets)
    all_words = re.sub(r'[^\w\s]', '', all_words).lower()  # Remove punctuation and lowercase
    word_list = all_words.split()
    stop_words = set(["the", "and", "is", "to", "a", "of", "in", "for", "on", "at", "with", "this", "that", "it", "as", "are", "was", "be"])
    filtered_words = [word for word in word_list if word not in stop_words]
    return Counter(filtered_words).most_common(num_words)

# Route: Homepage for file upload
@app.route('/')
def index():
    return render_template('index.html')

# Route: Handle CSV upload and analysis
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    # Read CSV and analyze sentiment
    tweets_df = pd.read_csv(file)
    if 'text' not in tweets_df.columns:
        return "Invalid CSV format. A 'text' column is required."

    tweets_df['Sentiment'] = tweets_df['text'].apply(analyze_sentiment)

    # Most common words
    most_common_words = get_most_common_words(tweets_df['text'])

    # Sentiment distribution
    sentiment_counts = tweets_df['Sentiment'].value_counts()

    # Generate sentiment distribution plot
    fig, ax = plt.subplots(figsize=(6, 6))
    sentiment_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax, colors=['#4CAF50', '#FFC107', '#F44336'])
    ax.set_ylabel('')
    ax.set_title('Sentiment Distribution')

    # Save plot to a string buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()

    # Render results
    return render_template(
        'results.html',
        plot_url=plot_data,
        tables=[tweets_df.to_html(classes='data')],
        most_common_words=most_common_words,
        sentiment_counts=sentiment_counts.to_dict(),
        total_tweets=len(tweets_df)
    )



# Create basic templates
    with open(os.path.join('templates', 'index.html'), 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Tweet Sentiment Analysis</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }
        header {
            background-color: #007bff;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .upload-form input[type="file"] {
            margin-bottom: 20px;
        }
        .upload-form button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 4px;
        }
        .upload-form button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <header>
        <h1>Tweet Sentiment Analysis</h1>
    </header>
    <div class="container">
        <form class="upload-form" action="/upload" method="post" enctype="multipart/form-data">
            <h2>Upload CSV File</h2>
            <input type="file" name="file" accept=".csv" required><br>
            <button type="submit">Analyze</button>
        </form>
    </div>
</body>
</html>

        ''')

    with open(os.path.join('templates', 'results.html'), 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Analysis Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }
        header {
            background-color: #007bff;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 800px;
            margin: 40px auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .chart {
            text-align: center;
            margin-bottom: 20px;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table th, table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        table th {
            background-color: #f2f2f2;
        }
        .summary {
            margin-bottom: 20px;
        }
        .summary h3 {
            color: #333;
        }
    </style>
</head>
<body>
    <header>
        <h1>Sentiment Analysis Results</h1>
    </header>
    <div class="container">
        <div class="chart">
            <h2>Sentiment Distribution</h2>
            <img src="data:image/png;base64,{{ plot_url }}" alt="Sentiment Distribution">
        </div>
        <div class="summary">
            <h3>Total Tweets: {{ total_tweets }}</h3>
            <h3>Sentiment Counts:</h3>
            <ul>
                {% for sentiment, count in sentiment_counts.items() %}
                <li>{{ sentiment }}: {{ count }}</li>
                {% endfor %}
            </ul>
            <h3>Most Common Words:</h3>
            <ul>
                {% for word, count in most_common_words %}
                <li>{{ word }}: {{ count }}</li>
                {% endfor %}
            </ul>
        </div>
        <div class="table-container">
            <h2>Detailed Tweet Data</h2>
            {{ tables|safe }}
        </div>
        <a href="/">Upload Another File</a>
    </div>
</body>
</html>

        ''')

    if __name__ == '__main__':
        # Ensure templates folder exists
        if not os.path.exists('templates'):
            os.makedirs('templates')

        # Run the app
        app.run(debug=True)
