#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from audioop import add
from dis import dis
import json
import sys
import dateutil.parser
from dateutil.parser import parse
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CSRFProtect
from forms import *
import os
from flask_migrate import Migrate
from models import Venue, db, Show, Artist

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db.init_app(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
#csrf = CSRFProtect(app)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')
  else:
      date = value
      return date

  

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  template_name = 'pages/home.html'
  return render_template(template_name)

#  GET LIST
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)


@app.route('/venues')
def venues():
  venues = Venue.query.all()
  data = []

  distinct_venues = Venue.query.distinct('city', 'state').all()
  
  for i in distinct_venues:
    venue_data = {}
    venue_data['city'] = i.city
    venue_data['state'] = i.state
    
    venue_data['venues'] = []
    for k in venues:
      venue_data_in = {}
      if k.state == i.state:
        venue_data_in['id'] = k.id
        venue_data_in['name'] = k.name
        venue_data['venues'].append(venue_data_in)

    data.append(venue_data)

  return render_template('pages/venues.html', areas=data);


@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for show in shows:
    show_data = {}
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    show_data['venue_id'] = show.venue_id
    show_data['venue_name'] = venue.name
    show_data['artist_id'] = show.artist_id
    show_data['artist_name'] = artist.name
    show_data['artist_image_link'] = artist.image_link
    show_data['start_time'] = show.start_time
    data.append(show_data)

  return render_template('pages/shows.html', shows=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  
  result = Venue.query.filter(
        Venue.name.ilike(f"%{search_term}%") |
        Venue.state.ilike(f"%{search_term}%") |
        Venue.city.ilike(f"%{search_term}%") 
    ).all()
  response={}
  data=[]
  for venue in result:
    data_val = {}
    data_val['id'] = venue.id
    data_val['name'] = venue.name
    data_val['num_upcoming_shows'] = 2 #Show.query.
    data.append(data_val)
    response['data'] = data
  response['count'] = len(result)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data_raw = Venue.query.get(venue_id)
  data = {}
  data['id'] = data_raw.id
  data['name'] = data_raw.name
  data['genres'] = data_raw.genres
  data['address'] = data_raw.address
  data['city'] = data_raw.city
  data['state'] = data_raw.state
  data['phone'] = data_raw.phone
  data['website'] = data_raw.website_link
  data['facebook_link'] = data_raw.facebook_link
  data['seeking_talent'] = data_raw.looking_for_talent
  data['seeking_description'] = data_raw.seeking_description
  data['image_link'] = data_raw.image_link

  now = datetime.now()
  data["past_shows"] = []
  data["upcoming_shows"] = []
  
  #past_shows = Show.query.filter(Show.venue_id==venue_id).filter(Show.start_time <= now).all()
  for show in data_raw.shows:
    if show.start_time <= now:
      show_data = {}
      show_data['id'] = show.id
      show_data['artist_name'] = show.artists.name
      show_data['artist_image_link'] = show.artists.image_link
      show_data['start_time'] = show.start_time
      data["past_shows"].append(show_data)

    else:
      show_data = {}
      show_data['id'] = show.id
      show_data['artist_name'] = show.artists.name
      show_data['artist_image_link'] = show.artists.image_link
      show_data['start_time'] = show.start_time
      data["upcoming_shows"].append(show_data)
      
  #upcoming_shows = Show.query.filter(Show.venue_id==venue_id).filter(Show.start_time >= now).all()
  
  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_venue.html', venue=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  search_term = request.form.get('search_term')
  
  result = Artist.query.filter(
        Artist.name.ilike(f"%{search_term}%") |
        Artist.state.ilike(f"%{search_term}%") |
        Artist.city.ilike(f"%{search_term}%") 
    ).all()
  response={}
  data=[]
  for artist in result:
    data_val = {}
    data_val['id'] = artist.id
    data_val['name'] = artist.name
    data_val['num_upcoming_shows'] = 2 #Show.query.
    data.append(data_val)
    response['data'] = data
  response['count'] = len(result)
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


# GET DETAIL

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data_raw = Artist.query.get(artist_id)
  
  data = {
    "id" : data_raw.id,
    "name" : data_raw.name,
    "genres": data_raw.genres,
    "city": data_raw.city,
    "state": data_raw.state,
    "phone": data_raw.phone,
    "website": data_raw.website_link,
    "facebook_link": data_raw.facebook_link,
    "seeking_venue": data_raw.seeking_venue,
    "seeking_description": data_raw.seeking_description,
    "image_link": data_raw.image_link,
  }
  now = datetime.now()
  data["past_shows"] = []
  data["upcoming_shows"] = []
  for show in data_raw.shows:
    if show.start_time >= now:
      show_data = {}
      show_data["venue_id"] = show.venue_id
      show_data["venue_name"] = show.venues.name
      show_data["venue_image_link"] = show.venues.image_link
      show_data["start_time"] = show.start_time
      data["past_shows"].append(show_data)
    else:
      show_data = {}
      show_data["venue_id"] = show.venue_id
      show_data["venue_name"] = show.venues.name
      show_data["venue_image_link"] = show.venues.image_link
      show_data["start_time"] = show.start_time
      data["upcoming_shows"].append(show_data)

  data["upcoming_shows_count"] = len(data["upcoming_shows"])
  data["past_shows_count"] = len(data["past_shows"])
    
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)


#  GET Create
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

#  POST Create
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  
  name = form.name.data
  city = form.city.data
  state = form.state.data
  address = form.address.data
  phone = form.phone.data
  genres = form.genres.data
  facebook_link = form.facebook_link.data
  website_link = form.website_link.data
  image_link = form.image_link.data
  seeking_talent = form.seeking_talent.data
  seeking_description = form.seeking_description.data

  venue_id = None
  error = False

  try:
    new_venue = Venue(
      name = name,
      city = city,
      state = state,
      address = address,
      phone = phone,
      genres = genres,
      facebook_link = facebook_link,
      website_link = website_link,
      image_link = image_link,
      looking_for_talent = True if seeking_talent == 'y' else False,
      seeking_description = seeking_description
    )

    db.session.add(new_venue)
    db.session.commit()
    venue_id = new_venue.id
  
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
      flash('Venue ' + request.form['name'] + ' could not be successfully listed!, Ensure all fields are filled')
      return redirect(url_for('create_venue_form'))
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('show_venue', venue_id=venue_id))


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  name = request.form.get('name')
  city = request.form.get('city')
  state = request.form.get('state')
  phone = request.form.get('phone')
  genres = request.form.getlist('genres')
  seeking_venue = request.form.get('seeking_venue')
  description = request.form.get('seeking_description')
  image_link = request.form.get('image_link')
  facebook_link = request.form.get('facebook_link')
  website_link = request.form.get('website_link')

  artist_id = None
  error = False
  print('look', seeking_venue)

  try:
    new_artist = Artist(
      name = name,
      city = city,
      state = state,
      phone = phone,
      genres = genres,
      facebook_link = facebook_link,
      image_link = image_link,
      website_link = website_link,
      seeking_venue = True if seeking_venue == 'y' else False,
      seeking_description = description
    )

    db.session.add(new_artist)
    db.session.commit()
    
    artist_id = new_artist.id
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  
  # on successful db insert, flash success
  
  if error:
    flash('Artist ' + request.form['name'] + ' could not be successfully listed!')
    return redirect(url_for('create_artist_form'))
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('show_artist', artist_id=artist_id))



@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  artist_id = request.form.get('artist_id')
  venue_id = request.form.get('venue_id')
  start_time = request.form.get('start_time')
  
  error = False
  try:
    new_show = Show(
      venue_id=venue_id,
      artist_id = artist_id,
      start_time = start_time
    )
    db.session.add(new_show)
    db.session.commit()
    
  except:
    error = True
    db.session.rollback()

  finally:
    db.session.close()

  if error:
    flash('Show could not be successfully listed!')
    return redirect(url_for('create_shows'))
  else:
    flash('Show was successfully listed!')
    return redirect(url_for('shows'))


#  GET UPDATE
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  genres = artist.genres.strip("{}")
  genres = list(genres.split(","))

  form.genres.process_data(genres)
  form.seeking_venue.process_data(artist.seeking_venue)
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  genres = venue.genres.strip("{}")
  genres = list(genres.split(","))
  form.genres.process_data(genres)
  form.seeking_talent.process_data(venue.looking_for_talent)
  return render_template('forms/edit_venue.html', form=form, venue=venue)


#  POST Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist_instance = Artist.query.get(artist_id)
  seeking_venue = request.form.get('seeking_venue')
  error = False
  
  try:
    artist_instance.seeking_venue = True if seeking_venue == 'y' else False
    form=ArtistForm(request.form, obj=artist_instance)
    form.populate_obj(artist_instance)
    print(request.form.get('seeking_description'))
    db.session.add(artist_instance)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    
  if error:
    flash("An error occured while trying to update the Artist!")
    return redirect(url_for('edit_artist_submission', artist_id=artist_id))
  else:
    flash("Artist updated successfully!")
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue_instance = Venue.query.get(venue_id)
  seeking_talent = request.form.get('seeking_talent')

  error = False
  try:
    venue_instance.looking_for_talent = True if seeking_talent == 'y' else False
    form=VenueForm(request.form, obj=venue_instance)
    form.populate_obj(venue_instance)

    db.session.add(venue_instance)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
    
  finally:
    db.session.close()

  if error:
    flash("An error occured while trying to update the venue!")
    return redirect(url_for('edit_venue_submission', venue_id=venue_id))
  else:
    flash("Venue updated successfully!")
    return redirect(url_for('show_venue', venue_id=venue_id))
    

#  DELETE
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()

  finally:
    db.session.close()
  
  if error:
    print(sys.exc_info())
    flash("Venue could not be deleted!")
    return redirect(url_for('index'))

  else:
    flash("Venue successfully deleted!")
    return redirect(url_for('index'))


@app.route("/artists/<artist_id>/delete", methods=["GET"])
def delete_artist(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash("Artist was not deleted successfully.")
  finally:
    db.session.close()

  if error:
    print(sys.exc_info())
    flash("Artist could not be deleted!")
    return redirect(url_for('index'))

  else:
    flash("Artist successfully deleted!")
    return redirect(url_for('index'))


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
'''
# Default port:
if __name__ == '__main__':
    app.run()
'''
# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
