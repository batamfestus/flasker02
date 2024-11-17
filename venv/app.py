from flask import Flask, render_template 



# To create a flask instance
app = Flask(__name__)


# create a route decorator
@app.route("/")
def index():
    first_name = "John"
    best_movies = ['Avatar', 'Game of throne', 'Originals', 'Bob hearts Abisola']
    return render_template("index.html", first_name=first_name, best_movies=best_movies)

@app.route("/user/<name>")
def user(name):
    return render_template("user.html", user_name=name)

# custom error pages
# invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template ("404.html"), 404
# internal server error
@app.errorhandler(500)
def server_error(e):
    return render_template ("500.html"), 500