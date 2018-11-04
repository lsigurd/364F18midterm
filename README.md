

MOVIE DATABASE APPLICATION README.md

This application provides a form for the user to input a movie and a rating (1-5) for that movie. After clicking submit, the resulting page has: 
	- A list of all the movies, ratings, and directors of those movies in the database
	- A list of top actors in every movie in the database
The application also provides a form for the user to input a rating (1-5). After clicking submit, the page refreshes so that all the movies in the database with this rating show below the form. 


The application has the following routes, each of which renders the template listed here:

http://localhost:5000/ -> index.html
http://localhost:5000/result -> result.html
http://localhost:5000/actors -> actors.html
http://localhost:5000/directors -> directors.html
