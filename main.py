from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,IntegerField
from wtforms.validators import DataRequired
import requests
import os

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("key")
Bootstrap5(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db.init_app(app)

class Edit(FlaskForm):
    review = StringField("review", validators=[DataRequired()])
    rating = IntegerField("rating", validators=[DataRequired()])
    submit = SubmitField("Submit")


class AddMovie(FlaskForm):
    movie_name = StringField("title",validators=[DataRequired()])
    submit = SubmitField("Submit")

# CREATE DB
class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

# CREATE TABLE
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movies).order_by(Movies.rating.desc()))
    all_movies = result.scalars().all() # convert ScalarResult to Python List

    for i in range(len(all_movies)):
        all_movies[i].ranking =  i+1
    db.session.commit()

    return render_template("index.html", movies=all_movies)    

   
@app.route("/add",methods = ["GET","POST"])
def add_movie():
    form = AddMovie()
    api_key = os.getenv("api_key")
    movie_title = form.movie_name.data
    url = f"http://www.omdbapi.com/?apikey={api_key}&t={movie_title}"

    if form.validate_on_submit():
        
        response = requests.get(url=url)
        data = response.json()    
        if data["Response"] == 'False':
            return render_template("add.html",not_found = True,form = form)
        movie = Movies(
            title = data["Title"],
            year = data["Year"],
            img_url = data['Poster'],
            rating = data["imdbRating"],
            description = data["Plot"],
            review = data["Genre"]
        )        
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add.html",form = form)

@app.route("/edit.html",methods = ["GET","POST"])
def edit():
    form = Edit()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movies, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html",movie = movie,form = form) 

@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movies, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))
if __name__ == '__main__':
    app.run(debug=True)
