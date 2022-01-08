from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests
import os

TMDB_API_KEY = '39356401f10209e14a4873c35c8d9664'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///movies.db")
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Bootstrap(app)

class Movie(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.INTEGER, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.FLOAT, nullable=False)
    ranking = db.Column(db.String(30), nullable=True)
    review = db.Column(db.String(500), nullable=True)
    img_url = db.Column(db.String(400), nullable=False)


db.create_all()

# db.session.add(new_movie)
# db.session.commit()

class Edit_Movie(FlaskForm):
    new_rating = FloatField("Your rating out of 10 e.g. 7.6",
                            validators=[DataRequired(), NumberRange(min=1,
                                                                    max=10, message='Maximum rate is 10, minimum 0.')],
                            render_kw={"placeholder": "new rating ..."})
    new_review = StringField("Your review", validators=[DataRequired()], render_kw={"placeholder": "new review ..."})
    submit = SubmitField('Done')

class Add_Movie(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()], render_kw={"placeholder": "movie name ..."})
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=["POST", "GET"])
def edit():
    edit_form = Edit_Movie()

    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    if request.method == "POST" and edit_form.validate_on_submit():
        movie_edited = Movie.query.get(movie_id)
        movie_edited.rating = edit_form.new_rating.data
        movie_edited.review = edit_form.new_review.data
        db.session.commit()
        all_movies = Movie.query.order_by(Movie.rating).all()
        # This line loops through all the movies
        for i in range(len(all_movies)):
            # This line gives each movie a new ranking reversed from their order in all_movies
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
        return render_template("index.html", movies=all_movies)
    return render_template("edit.html", form=edit_form, movie=movie_selected)

@app.route("/delete", methods=["POST", "GET"])
def delete():
    movie_id = request.args.get('id')
    movie_deleted = Movie.query.get(movie_id)
    db.session.delete(movie_deleted)
    all_movies = Movie.query.order_by(Movie.rating).all()
    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route('/add', methods=["POST", "GET"])
def add():
    add_form = Add_Movie()
    if add_form.validate_on_submit() and request.method == "POST":
        movie_to_search = add_form.movie_title.data
        response = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=en-US'
                                f'&include_adult=false&query={movie_to_search}').json()
        results = response['results']
        return render_template("select.html", results=results)
    return render_template("add.html", form=add_form)

@app.route("/find", methods=["POST", "GET"])
def find_movie():
    movie_id = request.args.get('id')
    if movie_id:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US')
        data = response.json()
        # Create a record
        new_movie = Movie(
            id=data['id'],
            title=data['title'],
            img_url=f"https://image.tmdb.org/t/p/original{data['poster_path']}",
            year=data['release_date'].split('-')[0],
            description=data['overview'],
            rating=data['vote_average'],
            ranking="None",
            review="None",
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
