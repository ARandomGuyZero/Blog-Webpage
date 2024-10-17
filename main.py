"""
Blog Webpage

Author: Alan
Date: October 16th 2024

This application uses Flask to show a webpage that uses Bootstrap for design and a json for the data.
"""

from flask import Flask, render_template
from requests import get
from post import Post

# Gets the data of the post
posts = get(url="https://api.npoint.io/dfae0d41493794c77072").json()

# Sets a post list empty
post_list = []

# For each post in post
for post in posts:

    # Save a new post object using data from the json
    post_obj = Post(post["id"], post["body"], post["title"], post["subtitle"], post["image_url"])

    # And then append it to the post list
    post_list.append(post_obj)

app = Flask(__name__)

@app.route('/')
def index():
    """
    Renders index.html file
    :return:
    """
    return render_template("index.html", posts=posts)

@app.route('/post/<int:index_number>')
def post(index_number):
    """
    Renders post.html file using an index number to post a certain post.
    :param index_number:
    :return:
    """

    # Set none as default
    required_post = None

    # For each post item in the post_list
    for post_item in post_list:

        # If the post_item id is the same as the index_number, will save the required post as an index
        if post_item.id == index_number:

            # Store the required post
            required_post = post_item
            break

    return render_template("post.html", post=required_post)

@app.route('/about')
def about():
    """
    Renders about.html file
    :return:
    """
    return render_template("about.html")

@app.route('/contact')
def contact():
    """
    Renders contact.html file
    :return:
    """
    return render_template("contact.html")

# Start the flask application
if __name__ == "__main__":
    app.run(debug=True)