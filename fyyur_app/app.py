#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app, session_options={'expire_on_commit': False})
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.String(120))
    show = db.relationship("Show", backref="venue", lazy=True)
    
    def __repr__(self):
      return f'{self.name}'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    show = db.relationship("Show", backref="artist", lazy=True)

    def __repr__(self):
      return f'Artist {self.name}'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
  __tablename__ = 'Shows'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  starting_time = db.Column(db.String(120), nullable=False)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  cities = [value[0] for value in db.session.query(Venue.city).distinct()]
  for city in cities:
    venues = Venue.query.filter(Venue.city == city).all()
    state = venues[0].state
    vens = []
    for venue in venues:
      idi = venue.id
      name = venue.name
      num_upcoming_shows = 0
      shows = Show.query.filter(Show.venue_id == venue.id).all()
      for show in shows:
        if show.starting_time > datetime.now():
          num_upcoming_shows += 1
      vens.append({
          'id': idi,
          'name': name,
          'num_upcoming_shows': num_upcoming_shows
         })
    data.append({
        'city': city,
        'state': state,
        'venues': vens
         })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on artists with partial string search. that is case-insensitive.
  # ex: seach for Hop should return "The Musical Hop".
  # ex:search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []
  for search_result in search_results:
    data.append({
        "id": search_result.id,
        "name": search_result.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == search_result.id).filter(Show.starting_time > datetime.now()).all()),
    })

  response = {
      "count": len(search_results),
      "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  data = []
  for venue in Venue.query.all():
    shows = db.session.query(Show).filter(Show.venue_id == venue.id).all()
    upcoming_shows_count = 0
    upcoming_shows = []
    past_shows = []
    past_shows_count = 0
    for show in shows:

      if show.starting_time > datetime.now():
                  upcoming_shows_count += 1
                  upcoming_shows.append({
        
                      "artist_id": show.artist_id,
                      "artist_name": show.artist.name,
                      "artist_image_link": show.artist.image_link,
                      "start_time": show.starting_time.isoformat()})
      else:
        past_shows_count += 1
        past_shows.append({

          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": show.starting_time.isoformat()})

    data.append({
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count})
  
  data = list(filter(lambda d: d['id'] == venue_id, data))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  # on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  # on successful db insert, flash success
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue_to_delete = Venue.query.get(venue_id)
  db.session.delete(venue_to_delete)
  db.session.commit()

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. That is case-insensitive.
  # Ex1:seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # Ex2:search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Artist).filter(
      Artist.name.ilike(f'%{search_term}%')).all()
  data = []
  for search_result in search_results:
    data.append({
        "id": search_result.id,
        "name": search_result.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == search_result.id).filter(Show.starting_time > datetime.now()).all()),
    })

  response = {
      "count": len(search_results),
      "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  data = []
  for artist in Artist.query.all():
    shows = db.session.query(Show).filter(Show.artist_id == artist.id).all()
    upcoming_shows_count = 0
    upcoming_shows = []
    past_shows = []
    past_shows_count = 0
    for show in shows:
      if show.starting_time > datetime.now():
          upcoming_shows_count += 1
          upcoming_shows.append({

              "venue_id": show.venue_id,
              "venue_name": show.venue.name,
              "venue_image_link": show.venue.image_link,
              "start_time": show.starting_time.isoformat()})
      else:
        past_shows_count += 1
        past_shows.append({

            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.starting_time.isoformat()})

    data.append({
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count})

  data = list(filter(lambda d: d['id'] == artist_id, data))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_to_edit = Artist.query.get(artist_id)
  form.name.data = artist_to_edit.name
  form.city.data = artist_to_edit.city
  form.state.data = artist_to_edit.state
  form.phone.data = artist_to_edit.phone
  form.genres.data = artist_to_edit.genres
  form.image_link.data = artist_to_edit.image_link
  
  return render_template('forms/edit_artist.html', form=form, artist=artist_to_edit)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # artist record with ID <artist_id> using the new attributes
  error = False
  artist_to_edit = Artist.query.get(artist_id)
  try:
    artist_to_edit.name = request.form['name']
    artist_to_edit.city = request.form['city']
    artist_to_edit.state = request.form['state']
    artist_to_edit.phone = request.form['phone']
    artist_to_edit.genres = request.form.getlist('genres')
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  # on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error occurred. Artist could not be changed.')
  # on successful db insert, flash success
  if not error:
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_to_edit = Venue.query.get(venue_id)
  form.name.data = venue_to_edit.name
  form.city.data = venue_to_edit.city
  form.state.data = venue_to_edit.state
  form.phone.data = venue_to_edit.phone
  form.genres.data = venue_to_edit.genres
  form.image_link.data = venue_to_edit.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue_to_edit)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # venue record with ID <venue_id> using the new attributes
  error = False
  venue_to_edit = Venue.query.get(venue_id)
  try:
    venue_to_edit.name = request.form['name']
    venue_to_edit.city = request.form['city']
    venue_to_edit.state = request.form['state']
    venue_to_edit.phone = request.form['phone']
    venue_to_edit.genres = request.form.getlist('genres')

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  # on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error occurred. venue could not be changed.')
  # on successful db insert, flash success 
  if not error:
    flash('venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    new_artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres)
    db.session.add(new_artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  # on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  # on successful db insert, flash success
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shs = Show.query.all()
  data =[]
  for show in shs:
    data.append({
      "venue_id":  show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.starting_time.isoformat()
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    starting_time = request.form['start_time']
    new_show = Show(artist_id=artist_id, venue_id=venue_id, starting_time=starting_time)
    db.session.add(new_show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  # on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error occurred. Show  could not be listed.')
  # on successful db insert, flash success
  if not error:
      flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
