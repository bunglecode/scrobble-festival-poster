from flask import url_for
import pylast
from PIL import Image, ImageFont, ImageDraw, ImageOps
import json
from flask import Flask, request, redirect, render_template, make_response
import requests
from urllib.parse import quote
import os
from functools import wraps, update_wrapper
import datetime
import config
import urllib.request
from werkzeug.exceptions import BadRequest
import string
import time
from path import Path

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "https://poster.bunglehub.com"
REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
SCOPE = "user-top-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": config.CLIENT_ID
}


@app.route("/", methods=['GET', 'POST'])
def home():

    one_day = time.time() - 600
    base = Path('/home/virtual/vps-5f29e5/0/0fda52cbb6/public_html/poster/static/posters')
    
    # Remove all generated posters older than one day from the directory
    
    for somefile in base.walkfiles():
        if somefile.mtime < one_day:
            somefile.remove()

    return render_template("index.html")


@app.route("/spot_form", methods=['GET', 'POST'])
def spot_form():

    timeframe = ['short_term', 'medium_term', 'long_term']

    return render_template("spot_form.html", timeframe=timeframe)


@app.route("/spotify", methods=['GET', 'POST'])
def spotifyauth():

    try:
        # Auth Step 1: Authorization
        url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
        auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
        return redirect(auth_url)
    except BadRequest:
        return render_template('fail.html')


@app.route("/callback/q")
def callback():

    spotifyauth()

    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': config.CLIENT_ID,
        'client_secret': config.CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    try:
        access_token = response_data["access_token"]
    except KeyError:
        return render_template('fail.html')
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    
    resp = make_response(render_template('loading.html'))
    resp.set_cookie('token', access_token)

    return resp


@app.route("/spot-poster", methods=['GET', 'POST'])
def spotposter():

    if request.method == 'POST':
        timeframe = request.form['tf']
        poster_template = request.form['template']

    # Auth Step 6: Use the access token to access Spotify API
    
    access_token = request.cookies.get('token')
    
    try:
        authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    except NameError:
        return render_template("fail.html")

    # Get user data
    username_profile = '{}/me'.format(SPOTIFY_API_URL)
    username_response = requests.get(username_profile, headers=authorization_header)
    username_data = json.loads(username_response.text)
    username = username_data['display_name']
    safechars = string.ascii_lowercase + string.ascii_uppercase + string.digits + ".-_"
    safe_username = ''.join([c for c in username if c in safechars])

    # Get profile data (top artists)
    user_profile_api_endpoint = "{}/me/top/artists".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get profile data (top tracks)
    user_profile_api_endpoint_tracks = "{}/me/top/tracks".format(SPOTIFY_API_URL)
    profile_response_tracks = requests.get(user_profile_api_endpoint_tracks, headers=authorization_header)

    # Get top tracks
    tracks_api_endpoint = "{}/me/top/tracks?limit=15&time_range={}".format(SPOTIFY_API_URL, timeframe)
    tracks_response = requests.get(tracks_api_endpoint, headers=authorization_header)
    top_tracks_data = json.loads(tracks_response.text)

    # Combine profile and top tracks data to display
    top_tracks_arr = top_tracks_data['items']
    number = 0
    track_list = []
    uri_list = []
    for track in top_tracks_arr:
        track = top_tracks_arr[number]['name']
        artist = top_tracks_arr[number]['artists'][0]['name']
        uri = top_tracks_arr[number]['id']
        track_list.append(f'{artist} - {track}')
        uri_list.append(uri)
        number += 1

    # Get top artists
    artist_api_endpoint = "{}/me/top/artists?limit=50&time_range={}".format(SPOTIFY_API_URL, timeframe)
    artists_response = requests.get(artist_api_endpoint, headers=authorization_header)
    top_artists_data = json.loads(artists_response.text)

    url1 = top_artists_data['items'][0]['images'][1]['url']
    urllib.request.urlretrieve(url1, 'static/artist_temp/temp1.png')

    url2 = top_artists_data['items'][1]['images'][1]['url']
    urllib.request.urlretrieve(url2, 'static/artist_temp/temp2.png')

    url3 = top_artists_data['items'][2]['images'][1]['url']
    urllib.request.urlretrieve(url3, 'static/artist_temp/temp3.png')

    # Combine profile and top artists data to display
    display_arr = top_artists_data['items']
    number = 0
    artist_list = []
    for item in display_arr:
        artist = display_arr[number]['name']
        artist_list.append(artist)
        number += 1

    def getLength(*args):
        total = 0
        for a in args:
            length = font.getlength(str(a))
            total += length
        return total
    try:
        a1 = artist_list[0]
        a2 = artist_list[1]
        a3 = artist_list[2]
        a4 = artist_list[3]
        a5 = artist_list[4]
        a6 = artist_list[5]
        a7 = artist_list[6]
        a8 = artist_list[7]
        a9 = artist_list[8]
        a10 = artist_list[9]
        a11 = artist_list[10]
        a12 = artist_list[11]
        a13 = artist_list[12]
        a14 = artist_list[13]
        a15 = artist_list[14]
        a16 = artist_list[15]
        a17 = artist_list[16]
        a18 = artist_list[17]
        a19 = artist_list[18]
        a20 = artist_list[19]
        a21 = artist_list[20]
        a22 = artist_list[21]
        a23 = artist_list[22]
        a24 = artist_list[23]
        a25 = artist_list[24]
        a26 = artist_list[25]
        a27 = artist_list[26]
        a28 = artist_list[27]
        a29 = artist_list[28]
        a30 = artist_list[29]
        a31 = artist_list[30]
        a32 = artist_list[31]
        a33 = artist_list[32]
        a34 = artist_list[33]
        a35 = artist_list[34]
        a36 = artist_list[35]
        a37 = artist_list[36]
        a38 = artist_list[37]
        a39 = artist_list[38]
    except IndexError:
        return render_template('not_enough_artists.html')

    if os.path.exists("static/base/{}.png".format(poster_template)):
        img = Image.open("static/base/{}.png".format(poster_template))

        color = (253, 227, 206)
        stroke_width = 8
        stroke_fill = (49, 54, 57)
        stroke_width_username = 3
        stroke_fill_username = (49, 54, 57)

        if poster_template == 'SF-6':
            color = (49, 54, 57)
            stroke_width = 8
            stroke_fill = (253, 227, 206)
            stroke_width_username = 3
            stroke_fill_username = (255, 255, 255)

        fontType = "static/fonts/arial-unicode-ms.ttf"

        # Username
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(fontType, 120)
        draw.text((900, 2210), "{}".format(username), color, stroke_width=stroke_width_username,
                  stroke_fill=stroke_fill_username, font=font, anchor="mm")
        
        #Timeframe
        if timeframe == 'long_term':
            tf_poster = 'All Time'
        elif timeframe == 'medium_term':
            tf_poster = '6 Months'
        elif timeframe == 'short_term':
            tf_poster = '4 Weeks'
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(fontType, 40)
        draw.text((900, 2310), "Spotify - {}".format(tf_poster), color, stroke_width=stroke_width_username, stroke_fill=stroke_fill_username, font=font, anchor="mm")

        # Dates
        fontSizeDates = 38

        friday = datetime.date.today()
        while friday.weekday() != 4:
            friday += datetime.timedelta(1)
        saturday = friday + datetime.timedelta(1)
        sunday = friday + datetime.timedelta(2)
        friday = friday.strftime("%b %d")
        saturday = saturday.strftime("%b %d")
        sunday = sunday.strftime("%b %d")
        font = ImageFont.truetype(fontType, fontSizeDates)
        draw.text((1366, 466), "Fri {}".format(friday).upper(), "white", font=font, anchor="lm")
        draw.text((190, 913), "Sat {}".format(saturday).upper(), "white", font=font, anchor="lm")
        draw.text((1365, 1366), "Sun {}".format(sunday).upper(), "white", font=font, anchor="lm")

        # 1st
        fontSizeHeadliner = 100
        font = ImageFont.truetype(fontType, fontSizeHeadliner)
        while getLength(a1) > 1400:
            fontSizeHeadliner = fontSizeHeadliner - 10
            font = ImageFont.truetype(fontType, fontSizeHeadliner)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 460), "{}".format(a1), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font,
                      anchor="lm")

        # 2nd
        fontSizeHeadliner = 100
        font = ImageFont.truetype(fontType, fontSizeHeadliner)
        while getLength(a2) > 1000:
            fontSizeHeadliner = fontSizeHeadliner - 10
            font = ImageFont.truetype(fontType, fontSizeHeadliner)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((1700, 905), "{}".format(a2), color, stroke_width=stroke_width, stroke_fill=stroke_fill,
                      font=font, anchor="rm")

        # 3rd
        fontSizeHeadliner = 100
        font = ImageFont.truetype(fontType, fontSizeHeadliner)
        while getLength(a3) > 1000:
            fontSizeHeadliner = fontSizeHeadliner - 10
            font = ImageFont.truetype(fontType, fontSizeHeadliner)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 1365), "{}".format(a3), color, stroke_width=stroke_width, stroke_fill=stroke_fill,
                      font=font, anchor="lm")

        # 4th / 5th / 6th / 7th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a4, a5, a6, a7)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 560), "{} · {} · {} · {}".format(a4, a5, a6, a7), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="lm")

        # 8th / 9th / 10th / 11th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a8, a9, a10, a11)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((1700, 1010), "{} · {} · {} · {}".format(a8, a9, a10, a11), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="rm")

        # 12th / 13th / 14th / 15th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a12, a13, a14, a15)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 1465), "{} · {} · {} · {}".format(a12, a13, a14, a15), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="lm")

        # 16th / 17th / 18th / 19th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a16, a17, a18, a19)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 640), "{} · {} · {} · {}".format(a16, a17, a18, a19), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="lm")

        # 20th / 21st / 22nd / 23rd
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a20, a21, a22, a23)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((1700, 1100), "{} · {} · {} · {}".format(a20, a21, a22, a23), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="rm")

        # 24th / 25th / 26th / 27th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a24, a25, a26, a27)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 1553), "{} · {} · {} · {}".format(a24, a25, a26, a27), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="lm")

        # 28th / 29th / 30th / 31st
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a28, a29, a30, a31)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 720), "{} · {} · {} · {}".format(a28, a29, a30, a31), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="lm")

        # 32nd / 33rd / 34th / 35th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a32, a33, a34, a35)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((1700, 1185), "{} · {} · {} · {}".format(a32, a33, a34, a35), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="rm")

        # 36th / 37th / 38th / 39th
        fontSizeSupport = 60
        font = ImageFont.truetype(fontType, fontSizeSupport)
        while getLength("{} · {} · {} · {}".format(a36, a37, a38, a39)) > 1500:
            fontSizeSupport = fontSizeSupport - 5
            font = ImageFont.truetype(fontType, fontSizeSupport)
        else:
            draw = ImageDraw.Draw(img)
            draw.text((100, 1635), "{} · {} · {} · {}".format(a36, a37, a38, a39), color, stroke_width=stroke_width,
                      stroke_fill=stroke_fill, font=font, anchor="lm")

        # Paste first artist icon onto poster
        try:
            temp1 = Image.open("static/artist_temp/temp1.png")
            basewidth = 325
            temp1 = temp1.resize((basewidth, 325), Image.ANTIALIAS)
            temp1.putalpha(360)
            temp1.save("static/artist_temp/temp11.png")
            temp11 = Image.open("static/artist_temp/temp11.png")
            temp111 = ImageOps.expand(temp11, border=5, fill='black')
            temp111.save("static/artist_temp/temp111.png")
            temp111 = Image.open("static/artist_temp/temp111.png")

            img.paste(temp111, (740, 1780), temp111)

        except (ValueError, FileNotFoundError) as e:
            img.paste(1, (740, 1780, 1065, 2105))

        # Paste second artist icon onto poster
        try:
            temp2 = Image.open("static/artist_temp/temp2.png")
            basewidth = 250
            temp2 = temp2.resize((basewidth, 250), Image.ANTIALIAS)
            temp2.putalpha(360)
            temp2.save("static/artist_temp/temp22.png")
            temp22 = Image.open("static/artist_temp/temp22.png")
            temp222 = ImageOps.expand(temp22, border=5, fill='black')
            temp222.save("static/artist_temp/temp222.png")
            temp222 = Image.open("static/artist_temp/temp222.png")

            img.paste(temp222, (395, 1815), temp222)

        except (ValueError, FileNotFoundError) as e:
            img.paste(1, (395, 1815, 645, 2065))

        # Paste third artist icon onto poster
        try:
            temp3 = Image.open("static/artist_temp/temp3.png")
            basewidth = 250
            temp3 = temp3.resize((basewidth, 250), Image.ANTIALIAS)
            temp3.putalpha(360)
            temp3.save("static/artist_temp/temp33.png")
            temp33 = Image.open("static/artist_temp/temp33.png")
            temp333 = ImageOps.expand(temp33, border=5, fill='black')
            temp333.save("static/artist_temp/temp333.png")
            temp333 = Image.open("static/artist_temp/temp333.png")

            img.paste(temp333, (1150, 1815), temp333)

        except (ValueError, FileNotFoundError) as e:
            img.paste(1, (1150, 1815, 1400, 2065))

        # Delete temporary artist image files after imposed onto main poster
        try:
            os.remove("static/artist_temp/temp1.png")
            os.remove("static/artist_temp/temp11.png")
            os.remove("static/artist_temp/temp111.png")
            os.remove("static/artist_temp/temp2.png")
            os.remove("static/artist_temp/temp22.png")
            os.remove("static/artist_temp/temp222.png")
            os.remove("static/artist_temp/temp3.png")
            os.remove("static/artist_temp/temp33.png")
            os.remove("static/artist_temp/temp333.png")
        except FileNotFoundError:
            pass

        img.save('static/posters/{}_{}_spotifyfestival.png'.format(safe_username, timeframe))
        imageFile = url_for('static', filename=f"posters/{safe_username}_{timeframe}_spotifyfestival.png")

        return render_template("poster.html", imageFile=imageFile, username=username, track_list=track_list, uri_list=uri_list)


@app.route('/form')
def form():

    timeframe = ['7day', '1month', '3month', '6month', '12month', 'overall']

    return render_template('form.html', timeframe=timeframe)


@app.route("/poster", methods=['POST', 'GET'])
def poster():

    try:
        def getLength(*args):
            total = 0
            for a in args:
                length = font.getlength(str(a))
                total += length
            return total

        if request.method != 'POST':
            return render_template('index.html')

        if request.method == 'POST':
            username = request.form['field1']
            poster_template = request.form['template']
            try:
                timeframe = request.form['tf']
            except KeyError:
                return render_template('fail.html')

            API_KEY = config.API_KEY
            API_SECRET = config.API_SECRET

            network = pylast.LastFMNetwork(
                api_key=API_KEY,
                api_secret=API_SECRET,
                username=username,
            )

            try:
                user = network.get_user(username)
            except pylast.WSError:
                return render_template("fail.html")
            topArtists = user.get_top_artists(period=timeframe)
            try:
                a1 = topArtists[0][0]
                a2 = topArtists[1][0]
                a3 = topArtists[2][0]
                a4 = topArtists[3][0]
                a5 = topArtists[4][0]
                a6 = topArtists[5][0]
                a7 = topArtists[6][0]
                a8 = topArtists[7][0]
                a9 = topArtists[8][0]
                a10 = topArtists[9][0]
                a11 = topArtists[10][0]
                a12 = topArtists[11][0]
                a13 = topArtists[12][0]
                a14 = topArtists[13][0]
                a15 = topArtists[14][0]
                a16 = topArtists[15][0]
                a17 = topArtists[16][0]
                a18 = topArtists[17][0]
                a19 = topArtists[18][0]
                a20 = topArtists[19][0]
                a21 = topArtists[20][0]
                a22 = topArtists[21][0]
                a23 = topArtists[22][0]
                a24 = topArtists[23][0]
                a25 = topArtists[24][0]
                a26 = topArtists[25][0]
                a27 = topArtists[26][0]
                a28 = topArtists[27][0]
                a29 = topArtists[28][0]
                a30 = topArtists[29][0]
                a31 = topArtists[30][0]
                a32 = topArtists[31][0]
                a33 = topArtists[32][0]
                a34 = topArtists[33][0]
                a35 = topArtists[34][0]
                a36 = topArtists[35][0]
                a37 = topArtists[36][0]
                a38 = topArtists[37][0]
                a39 = topArtists[38][0]
                a40 = topArtists[39][0]
                a41 = topArtists[40][0]
                a42 = topArtists[41][0]
                a43 = topArtists[42][0]
                a44 = topArtists[43][0]
                a45 = topArtists[44][0]
                a46 = topArtists[45][0]
                a47 = topArtists[46][0]
                a48 = topArtists[47][0]
                a49 = topArtists[48][0]
            except IndexError:
                return render_template('not_enough_artists.html')

            topTracks = user.get_top_tracks(period=timeframe)
            topTracks_list = []
            number = 0
            for track in topTracks:
                track = topTracks[number][0]
                topTracks_list.append(track)
                number += 1

            topTracks_list = topTracks_list[:15]

            if os.path.exists("static/base/{}.png".format(poster_template)):
                img = Image.open("static/base/{}.png".format(poster_template))

                color = (253, 227, 206)
                stroke_width = 8
                stroke_fill = (49, 54, 57)
                stroke_width_username = 8
                stroke_fill_username = (49, 54, 57)

                if poster_template == 'SF-6':
                    color = (49, 54, 57)
                    stroke_width = 8
                    stroke_fill = (253, 227, 206)
                    stroke_width_username = 8
                    stroke_fill_username = (253, 227, 206)

                fontType = "static/fonts/arial-unicode-ms.ttf"

                # Username
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype(fontType, 120)
                draw.text((900, 2200), "{}".format(user), color, stroke_width=stroke_width_username, stroke_fill=stroke_fill_username, font=font, anchor="mm")
                
                #Timeframe
                if timeframe == '7day':
                    tf_poster = '1 Week'
                elif timeframe == '1month':
                    tf_poster = '1 Month'
                elif timeframe == '3month':
                    tf_poster = '3 Months'
                elif timeframe == '6month':
                    tf_poster = '6 Months'
                elif timeframe == '12month':
                    tf_poster = '12 Months'
                elif timeframe == 'overall':
                    tf_poster = 'All Time'
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype(fontType, 40)
                draw.text((900, 2315), "Last.fm - {}".format(tf_poster), color, stroke_width=stroke_width_username, stroke_fill=stroke_fill_username, font=font, anchor="mm")

                # Dates
                fontSizeDates = 38

                friday = datetime.date.today()
                while friday.weekday() != 4:
                    friday += datetime.timedelta(1)
                saturday = friday + datetime.timedelta(1)
                sunday = friday + datetime.timedelta(2)
                friday = friday.strftime("%b %d")
                saturday = saturday.strftime("%b %d")
                sunday = sunday.strftime("%b %d")
                font = ImageFont.truetype(fontType, fontSizeDates)
                draw.text((1366, 466), "Fri {}".format(friday).upper(), "white", font=font, anchor="lm")
                draw.text((190, 913), "Sat {}".format(saturday).upper(), "white", font=font, anchor="lm")
                draw.text((1365, 1366), "Sun {}".format(sunday).upper(), "white", font=font, anchor="lm")

                # 1st
                fontSizeHeadliner = 100
                font = ImageFont.truetype(fontType, fontSizeHeadliner)
                while getLength(a1) > 1400:
                    fontSizeHeadliner = fontSizeHeadliner - 10
                    font = ImageFont.truetype(fontType, fontSizeHeadliner)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 460), "{}".format(a1), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font,  anchor="lm")

                # 2nd
                fontSizeHeadliner = 100
                font = ImageFont.truetype(fontType, fontSizeHeadliner)
                while getLength(a2) > 1000:
                    fontSizeHeadliner = fontSizeHeadliner - 10
                    font = ImageFont.truetype(fontType, fontSizeHeadliner)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((1700, 905), "{}".format(a2), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="rm")

                # 3rd
                fontSizeHeadliner = 100
                font = ImageFont.truetype(fontType, fontSizeHeadliner)
                while getLength(a3) > 1000:
                    fontSizeHeadliner = fontSizeHeadliner - 10
                    font = ImageFont.truetype(fontType, fontSizeHeadliner)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 1365), "{}".format(a3), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # 4th / 5th / 6th / 7th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a4, a5, a6, a7)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 560), "{} · {} · {} · {}".format(a4, a5, a6, a7), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # 8th / 9th / 10th / 11th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a8, a9, a10, a11)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((1700, 1010), "{} · {} · {} · {}".format(a8, a9, a10, a11), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="rm")

                # 12th / 13th / 14th / 15th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a12, a13, a14, a15)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 1465), "{} · {} · {} · {}".format(a12, a13, a14, a15), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # 16th / 17th / 18th / 19th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a16, a17, a18, a19)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 640), "{} · {} · {} · {}".format(a16, a17, a18, a19), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # 20th / 21st / 22nd / 23rd
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a20, a21, a22, a23)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((1700, 1100), "{} · {} · {} · {}".format(a20, a21, a22, a23), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="rm")

                # 24th / 25th / 26th / 27th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a24, a25, a26, a27)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 1550), "{} · {} · {} · {}".format(a24, a25, a26, a27), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # 28th / 29th / 30th / 31st
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a28, a29, a30, a31)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 720), "{} · {} · {} · {}".format(a28, a29, a30, a31), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # 32nd / 33rd / 34th / 35th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a32, a33, a34, a35)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((1700, 1185), "{} · {} · {} · {}".format(a32, a33, a34, a35), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="rm")

                # 36th / 37th / 38th / 39th
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {}".format(a36, a37, a38, a39)) > 1500:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 1635), "{} · {} · {} · {}".format(a36, a37, a38, a39), color, stroke_width=stroke_width, stroke_fill=stroke_fill, font=font, anchor="lm")

                # Introducing
                font = ImageFont.truetype(fontType, 75)
                draw.text((900, 1820), "· Introducing ·", color, stroke_width=stroke_width_username, stroke_fill=stroke_fill_username, font=font, anchor="mm")

                # 40 - 44
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {} · {}".format(a40, a41, a42, a43, a44)) > 1400:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((900, 1930), "{} · {} · {} · {} · {}".format(a40, a41, a42, a43, a44), color, stroke_width=stroke_width_username, stroke_fill=stroke_fill_username, font=font, anchor="mm")

                # 45 - 49
                fontSizeSupport = 60
                font = ImageFont.truetype(fontType, fontSizeSupport)
                while getLength("{} · {} · {} · {} · {}".format(a45, a46, a47, a48, a49)) > 1400:
                    fontSizeSupport = fontSizeSupport - 5
                    font = ImageFont.truetype(fontType, fontSizeSupport)
                else:
                    draw = ImageDraw.Draw(img)
                    draw.text((900, 2020), "{} · {} · {} · {} · {}".format(a45, a46, a47, a48, a49), color, stroke_width=stroke_width_username, stroke_fill=stroke_fill_username, font=font, anchor="mm")

                img.save('static/posters/{}_{}_lastfmfestival.png'.format(username, timeframe))
                imageFile = url_for('static', filename="posters/{}_{}_lastfmfestival.png".format(username, timeframe))

                return render_template('poster.html', imageFile=imageFile, username=username, topTracks_list=topTracks_list)
    except BadRequest:
        return render_template('fail.html')


if __name__ == "__main__":
    app.run()
