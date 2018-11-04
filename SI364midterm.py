###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, RadioField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell 
import requests
import json

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values

app.config['SECRET_KEY'] = 'hard to guess string from si364'
## TODO 364: Create a database in postgresql in the code line below, and fill in your app's database URI. It should be of the format: postgresql://localhost/YOUR_DATABASE_NAME

##Postgres database is "lsigurdMidterm"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://laurensigurdson@localhost:5432/lsigurdMidterm"

## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


## Statements for db setup (and manager setup if using Manager)
manager = Manager(app)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################



# Custom validation for this form so that the movie name is at least 3 characters
def validate_movie_name(self, field):
    user_input = field.data
    if len(user_input) < 3:
        raise ValidationError("Your movie name must be at least 3 characters.")

##################
##### MODELS #####
##################

#Creating two tables (Movie and Director) which have a one to many relationship


class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    director_id = db.Column(db.Integer,db.ForeignKey("directors.id"))
    rating = db.Column(db.Integer)
    actors = db.relationship('Actor',backref='Movie') # building the relationship -- one movie, many actors

class Actor(db.Model):
    __tablename__ = "actors"
    id = db.Column(db.Integer, primary_key=True)
    actor_name = db.Column(db.String(64))
    movie_id = db.Column(db.Integer,db.ForeignKey("movies.id"))

class Director(db.Model):
    __tablename__ = "directors"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255))
    movies = db.relationship('Movie',backref='Director') # building the relationship -- one director, many movies


###################
###### FORMS ######
###################



class MovieForm(FlaskForm):
    movie_name = StringField("Please enter a movie name (must be at least 3 characters): ",validators=[Required(), validate_movie_name])
    movie_rating = RadioField('How much do you like this movie? (1 low, 5 high)', choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], validators=[Required()])
    submit = SubmitField("Submit")

class RatingForm(FlaskForm):
    rating_search = IntegerField("Please enter a rating 1-5 to see all movies with this rating: ", validators=[Required()])
    submit = SubmitField("Submit")

def get_or_create_director(director_name):
    # Query the director table and filter using movie_name
    # If director exists, return the director object
    # Else add a new director to the Director table
    director_one = Director.query.filter_by(full_name = director_name).first()
    if director_one:
        return director_one
    else: 
        director_two = Director(full_name = director_name)
        db.session.add(director_two)
        db.session.commit()
        print ("added director successfully")
        return director_two


def get_or_create_movie(movie_title, director, rating):
    # Query the movie table using movie_title
    # If movie exists, return the movie object
    # Else add a new movie to the movie table.
    # NOTE : You will need director_id because that is the foreign key in the movie table.
    # So if you are adding a new movie, you will have to make a call to get_or_create_director function using director_name
    movie_query = Movie.query.filter_by(name = movie_title).first()
    if movie_query:
        return movie_query
    else:
        director_query = Director.query.filter_by(full_name = director).first()
        movie_one = Movie(name = movie_title, director_id = director_query.id, rating = rating)
        db.session.add(movie_one)
        db.session.commit()
        print ("added movie successfully")
        return movie_one

def get_or_create_actor(actor, movie):
    # Query the actor table using actor
    # If actor exists, return the actor object
    # Else add a new actor to the actor table.
    # NOTE : You will need movie_id because that is the foreign key in the actor table.
    # So if you are adding a new actor, you will have to make a call to get_or_create_movie function using movie_title
    actor_query = Actor.query.filter_by(actor_name = actor).first()
    if actor_query:
        return actor_query
    else: 
        movie_query = Movie.query.filter_by(name = movie).first()
        actor_one = Actor(actor_name = actor, movie_id = movie_query.id)
        db.session.add(actor_one)
        db.session.commit()
        print("added actor successfully")
        return actor_one



##################
##### Routes #####
##################

## Error handling route
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
    


#######################
###### VIEW FXNS ######
#######################


@app.route('/', methods=['GET', 'POST'])
def index():
    
    # Initialize the form
    form = MovieForm()

    if form.validate_on_submit():
        movie_name = form.movie_name.data
        movie_rating = form.movie_rating.data
        
        print(movie_name)
        print(movie_rating)

        baseurl = 'http://www.omdbapi.com/?apikey=9bdba9be'
        params = {}
        params["t"] = movie_name
        api_request = requests.get(baseurl, params = params)
        movie_dict = json.loads(api_request.text)

        print(movie_dict)

        if "Error" in movie_dict:
            flash("Please check your spelling or enter another movie. That movie was not found in the API")
            return render_template('index.html', form = form)
        else:
            director = str(movie_dict['Director'])
            actor_string = str(movie_dict['Actors'])
            actor_list = actor_string.split(",")
            
            print(director)
            print(actor_list)
            
            movie_query = Movie.query.filter_by(name = movie_name).first() 

            if movie_query:
                flash("someone already entered this movie in the database")
                return render_template('index.html', form = form)
            else:
                query_director = get_or_create_director(director)
                query_movie = get_or_create_movie(movie_name, director, movie_rating)
                for actor in actor_list:
                    query_actor = get_or_create_actor(actor, movie_name)
        
                flash("movie successfully added to the db")
                return redirect(url_for('form_result'))     


    search_form = RatingForm(request.args)
    search_results = None
    print(search_form.validate())
    if search_form.validate():
        print(search_form.rating_search.data)
        rating_search = int(search_form.rating_search.data)
        search_results = Movie.query.filter_by(rating = rating_search).all()
        print(search_results)
        if not search_results:
            flash("No results found for this rating")
            return render_template('index.html', search_form = search_form)
        else:
            print(search_results)


    # If the form did NOT validate / was not submitted
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html', form = form, search_form = search_form, results = search_results) 


@app.route('/result')
def form_result():
    all_movies = []
    all_actors = []
    movies = Movie.query.all()
    actors = Actor.query.all()
    for m in movies:
        director = Director.query.filter_by(id = m.director_id).first()
        all_movies.append((m.name, m.rating, director.full_name))
    
    for a in actors:
        movie = Movie.query.filter_by(id = a.movie_id).first()
        all_actors.append((a.actor_name, movie.name))
    
    return render_template('result.html', all_movies = all_movies, all_actors = all_actors)

@app.route('/actors')
def see_all_actors():
    all_actors = []
    actors = Actor.query.all()
    for a in actors:
        all_actors.append(a.actor_name)
    return render_template('actors.html', all_actors = all_actors)

@app.route('/directors')
def see_all_directors():
    all_directors = []
    directors = Director.query.all()
    for d in directors:
        all_directors.append(d.full_name)
    return render_template('directors.html', all_directors = all_directors)


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!

if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual


































