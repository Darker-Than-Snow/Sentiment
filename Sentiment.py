from flask import Flask, render_template, request, redirect, url_for, flash
from textblob import TextBlob
from collections import Counter
import re
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add a secret key for flash messages

def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.5:
        return "Excellent"
    elif analysis.sentiment.polarity > 0:
        return "Good"
    elif analysis.sentiment.polarity == 0:
        return "Neutral"
    else:
        return "Poor"


def get_most_common_words(tweets, num_words=10):
    all_words = ' '.join(tweets)
    all_words = re.sub(r'[^\w\s]', '', all_words).lower()
    word_list = all_words.split()
    stop_words = set([
        "the", "and", "is", "to", "a", "of", "in", "for", "on", "at", "with",
        "this", "that", "it", "as", "are", "was", "be", "bank"
    ])
    filtered_words = [word for word in word_list if word not in stop_words]
    return Counter(filtered_words).most_common(num_words)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or 'bank_name' not in request.form:
        flash('Please select a CSV file and enter a bank name.', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    bank_name = request.form['bank_name'].strip()

    if file.filename == '' or bank_name == '':
        flash('Please select a CSV file and enter a bank name.', 'error')
        return redirect(url_for('index'))

    try:
        df = pd.read_csv(file)
        if 'text' not in df.columns:
            flash("Invalid CSV format. A 'text' column is required.", 'error')
            return render_template('results.html')

        # Filter tweets mentioning the specified bank
        df = df[df['text'].str.contains(bank_name, case=False, na=False)]

        if df.empty:
            return render_template('results.html',
                                   error_message=f"No tweets mentioning {bank_name} found in the uploaded file.")

        # Analyze sentiment
        df['Sentiment'] = df['text'].apply(analyze_sentiment)

        # Calculate sentiment percentages
        sentiment_counts = df['Sentiment'].value_counts()
        total_tweets = len(df)
        positive_percentage = (sentiment_counts.get('Excellent', 0) + sentiment_counts.get('Good', 0)) / total_tweets * 100
        negative_percentage = sentiment_counts.get('Poor', 0) / total_tweets * 100
        neutral_percentage = sentiment_counts.get('Neutral', 0) / total_tweets * 100

        # Generate a rating based on positive sentiment percentage
        if positive_percentage > 75:
            rating = "Excellent"
        elif positive_percentage > 50:
            rating = "Good"
        elif positive_percentage > 25:
            rating = "Average"
        else:
            rating = "Poor"

        # Extract most common words
        positive_words = get_most_common_words(df[df['Sentiment'] == 'Excellent']['text'].tolist() + df[df['Sentiment'] == 'Good']['text'].tolist())
        negative_words = get_most_common_words(df[df['Sentiment'] == 'Poor']['text'].tolist())

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

        return render_template('results.html',
                               plot_url=plot_data,
                               positive_words=positive_words,
                               negative_words=negative_words,
                               sentiment_counts=sentiment_counts.to_dict(),
                               total_tweets=total_tweets,
                               positive_percentage=positive_percentage,
                               negative_percentage=negative_percentage,
                               neutral_percentage=neutral_percentage,
                               rating=rating,
                               bank_name=bank_name,
                               error_message=None)  # Clear error message
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return render_template('results.html', error_message=str(e))
if __name__ == '__main__':
    app.run(debug=True)