
# -*- coding: utf8 -*-

import os, random
from hashlib import md5
from datetime import datetime
from flask import Flask, request, render_template, redirect
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy

from myanmar import is_zawgyi, zg12uni51, is_myanmar

import cairo
import pango
import pangocairo

def create_app ():
    app = Flask(__name__)
    app.config.from_pyfile('config.cfg')
    Bootstrap(app)
    return app

app = create_app()
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    content = db.Column(db.String(360))
    pub_date = db.Column(db.DateTime)

    def __init__(self, post):
        self.content = post
        self.pub_date = datetime.utcnow()
        self.id = md5(post.encode('utf8') + str(self.pub_date)).hexdigest()

    def __repr__(self):
        return '<Post %r>' % self.content

class PostImage ():
    def __init__ (self, postid):
        post = Post.query.get_or_404(postid)
        parent_directory = os.path.join(app.root_path,
                                        'static',
                                        str(post.pub_date.date()))

        if not os.path.exists(parent_directory):
            try:
                os.makedirs(parent_directory)
            except OSError as e:
                app.logger.warning("Cannot mkdirs" + parent_directory + e)

        image_file = os.path.join(parent_directory, postid + '.png')
        #if not os.path.exists(image_file):
        self._create_image(image_file, post.content)

        self.imagepath = os.path.join('/static/',
                                 str(post.pub_date.date()),
                                 postid + '.png')

    @staticmethod
    def get_background_color ():
        return random.choice([
            (0.9372549019607843, 0.3254901960784314, 0.3137254901960784),
            (0.9411764705882353, 0.3843137254901961, 0.5725490196078431),
            (0.807843137254902, 0.5764705882352941, 0.8470588235294118),
            (0.7019607843137254, 0.615686274509804, 0.8588235294117647),
            (0.6235294117647059, 0.6588235294117647, 0.8549019607843137),
            (0.5647058823529412, 0.792156862745098, 0.9764705882352941),
            (0.1607843137254902, 0.7137254901960784, 0.9647058823529412),
            (0.14901960784313725, 0.7764705882352941, 0.8549019607843137),
            (0.30196078431372547, 0.7137254901960784, 0.6745098039215687),
            (0.5058823529411764, 0.7803921568627451, 0.5176470588235295),
            (0.5450980392156862, 0.7647058823529411, 0.2901960784313726),
            (0.803921568627451, 0.8627450980392157, 0.2235294117647059),
            (0.9921568627450981, 0.8470588235294118, 0.20784313725490197),
            (1.0, 0.7568627450980392, 0.027450980392156862),
            (1.0, 0.6549019607843137, 0.14901960784313725),
            (1.0, 0.4392156862745098, 0.2627450980392157),
            (0.7372549019607844, 0.6666666666666666, 0.6431372549019608),
            (0.7411764705882353, 0.7411764705882353, 0.7411764705882353),
            (0.6901960784313725, 0.7450980392156863, 0.7725490196078432)
        ])

    @classmethod
    def _create_image (cls, imagefile, post):
        WIDTH = 500
        PADDING = 20

        source = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, 800)
        sourcectx = cairo.Context(source)

        # background white
        sourcectx.set_source_rgb(*cls.get_background_color())
        sourcectx.paint()

        sourcectx.translate(PADDING, PADDING)
        pangoctx = pangocairo.CairoContext(sourcectx)
        pangoctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

        layout = pangoctx.create_layout()
        font = pango.FontDescription("Pyidaungsu")

        size = 1024 * 14
        font.set_size(size)
        layout.set_font_description(font)

        layout.set_text(post)
        layout.set_width(1024 * (WIDTH-2*PADDING))
        layout.set_wrap(pango.WRAP_CHAR)

        width, height = layout.get_size()
        width, height = width/1024, height/1024
        height = max(height, 200)

        sourcectx.set_source_rgb(0.1, 0.1, 0.1)
        pangoctx.update_layout(layout)
        pangoctx.show_layout(layout)

        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, height + 2*PADDING)
        surfacectx = cairo.Context(surface)
        surfacectx.set_source_surface(source)
        surfacectx.paint()

        surface.write_to_png(imagefile)

    def url (self):
        return self.imagepath

@app.route('/', methods=['GET', 'POST'])
def home_page():
    content = request.form.get('content', '')
    content = content.strip()
    if request.method == 'POST' and content:
        if is_myanmar(content) and is_zawgyi(content):
            print "converting to unicode"
            content = zg12uni51(content)

        post = Post(content)
        db.session.add(post)
        db.session.commit()

        return redirect ('/post/' + post.id)
    return render_template("home.html", name=__name__)

@app.route('/post/<postid>')
def post_page(postid):
    PostImage(postid)
    post = Post.query.get_or_404(postid)
    post.url = PostImage(postid).url()
    return render_template("post.html", post=post)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
