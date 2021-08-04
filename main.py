from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from os import getenv, environ
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('POSTGRE_DATABASE_URL', 'sqlite:///movies-collection.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)


MOVIES_API_KEY = getenv("API_KEY")
MOVIES_API_URL = "https://api.themoviedb.org/3/search/movie"


class Movie(db.Model):
    __tablename__ = "movie"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), unique=True, nullable=False)
    year = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(1020), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(320), nullable=True)
    image_url = db.Column(db.String(320), nullable=False)

    def __repr__(self):
        return '<Movie %r>' % self.title


db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit_btn = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit_btn = SubmitField("Add Movie")


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()

    for movie_index in range(len(all_movies)):
        all_movies[movie_index].ranking = len(all_movies) - movie_index

    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    movie_id = request.args.get("id", type=int)

    if form.validate_on_submit():
        movie_to_search_for = form.title.data

        params = {
            "api_key": MOVIES_API_KEY,
            "query": movie_to_search_for,
        }

        response = requests.get(MOVIES_API_URL, params=params)
        response.raise_for_status()
        search_results = response.json()["results"]

        return render_template('select.html', search_results=search_results)

    if movie_id is not None:
        movie_details_api_url = f"https://api.themoviedb.org/3/movie/{movie_id}"

        params = {
            "api_key": MOVIES_API_KEY,
        }

        response = requests.get(movie_details_api_url, params=params)
        title = response.json()["original_title"]
        img_url = f"https://image.tmdb.org/t/p/w500{response.json()['poster_path']}"
        year = response.json()["release_date"]
        description = response.json()["overview"]

        new_movie = Movie(title=title, year=year, description=description, image_url=img_url)
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for('edit', id=new_movie.id))

    return render_template("add.html", form=form)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    all_movies = Movie.query.all()
    passed_movie_id = int(request.args.get("id"))

    if form.validate_on_submit():
        movie_to_edit = Movie.query.get(passed_movie_id)
        new_rating = form.rating.data
        new_review = form.review.data

        movie_to_edit.rating = new_rating
        movie_to_edit.review = new_review

        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", movies=all_movies, id=passed_movie_id, form=form)


@app.route("/delete")
def delete():
    passed_movie_id = int(request.args.get("id"))
    movie_to_delete = Movie.query.get(passed_movie_id)

    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    # db.create_all()
    app.run()
