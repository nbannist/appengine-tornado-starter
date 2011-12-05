#!/usr/bin/env python
#
""" main.py
    Defined in app.yaml, by default this catches all calls to the application.
    
    The original import was this: 
    from google.appengine.ext import webapp # deleted this line
    from google.appengine.ext.webapp import util #deleted this line too
"""
import tornado.web
import tornado.wsgi
import wsgiref.handlers
"""Tornado Stuff"""

import os
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
"""Import the Jinja2 stuff"""

from docutils.core import publish_parts
import docutils.parsers.rst.directives.sourcecode
""" docutils """

import cgi
""" cgi for cgi.escape  for **simple** HTML escaping """

import markdown
""" Markdown """

import logging

class BaseHandler(tornado.web.RequestHandler):
    """BaseHandler
        -----------
        This base handler will make a convienent place to keep methods that are accessible from all handlers that inherit from this handler class. Currently, it is empty.
    """
    def render_rst(self, rst):
        """render_rst(self, rst)
            @self - the BaseHandler object
            @rst - the text to render into HTML
            
            http://andialbrecht.wordpress.com/2008/08/14/using-restructuredtext-on-app-engine/
            "By default, docutils tries to read configuration files from various locations. 
            But this will fail in the App Engine environment. 
        So you have to disable it by overwriting the default settings:"
        """
        parts = publish_parts(source=rst, writer_name='html4css1',
                       settings_overrides={'_disable_config': True})
        return parts['html_body'] # changed to return 'html_body' instead of 'fragment'; 'fragment' doesn't include beginning headings unless there is a paragraph before it.



    def get_all_rst_parts(self, rst):
        """get_all_rst_parts(self, rst)
            @self - the BaseHandler object
            @rst - the text to render
            We are returning the entire dictionary in this one.
        """
        # in this method we are returning the entire dict
        return publish_parts(source=rst, writer_name='html4css1',
                       settings_overrides={'_disable_config': True })

    def render_md(self, md):
        """render_md(self, md)
            self - BaseHandler
            md - raw markdown text
        """
        # code modified from http://www.joeyb.org/blog/2009/06/03/django-based-blog-on-google-app-engine-tutorial-part-2
 
        markdown_processor = markdown.Markdown(extensions=['codehilite']) # Setup Markdown with the code highlighter
        html = markdown_processor.convert(md) # Convert the md (markdown) into html
        # to mimic the same output as Docutils, I'm wrapping the output in a classed div.
        html = '<div class="document">'+html+'</div>'
        return html




class TemplateRendering:
    """TemplateRendering
       A simple class to hold methods for rendering templates. 
    """
    def render_template(self, template_name, variables):
        """render_template
            Returns the result of template.render to be used elsewhere. I think this will be useful to render templates to be passed into other templates.
        
            Gets the template directory from app settings dictionary with a fall back to "templates" as a default.
            
            Probably could use a default output if a template isn't found instead of throwing an exception.
        """
        template_dirs = []
        if self.settings["templates"] and self.settings["templates"] != '': 
            template_dirs.append(os.path.join(os.path.dirname(__file__),
            self.settings["templates"]))
        template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates')) # added a default for fail over.
        
        env = Environment(loader = FileSystemLoader(template_dirs))
        
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        content = template.render(variables)
        return content




# We don't inherit from webapp.RequestHandler anymore; MainHandler now extends BaseHandler, which extends tornado.web.RequestHandler
class MainHandler(BaseHandler, TemplateRendering):
    """MainHandler
        Extends from both BaseHandler and 
    """
    def get(self, *args):
        """GET Handler for MainHandler
        If "/" is requested with a HTTP GET, then this is the handler Tornado will execute.
        
        """
        variables = {'message':'Hello, Tornado!', 'page_title': self.settings["page_title"], 'page_description': '', 'page_author': 'The author of the page.', 'sourcecode_stylesheet': self.settings["sourcecode_stylesheet"], 'HTTPFUNCTION':'GET'}
        content = self.render_template('hello_world.html', variables)
        self.write(content)

    def post(self, *args):
        """POST handler for main. 
            If "/" is POSTed to then this is the handler Tornado will execute
        """
        # markdown/rst choice
        markup_type = self.get_argument('markup_type', default=u"rst")
        # raw markup
        raw_input = self.get_argument('markup_raw', default=u"")
        # reStructuredText/markdown stuff
        if markup_type:
            if markup_type == 'rst':
                html_output = self.render_rst(raw_input)
                # encode to iso-8859-1 to correct output.http://www.red-mercury.com/blog/eclectic-tech/python-unicode-fixing-utf-8-encoded-as-latin-1-iso-8859-1/  
                html_output_esc = html_output.encode('iso-8859-1')
                # encode to utf-8, split on new lines, re-join to single-line http://stackoverflow.com/questions/2201633/replace-newlines-in-a-unicode-string
                html_output_esc = ''.join(unicode(html_output_esc, 'utf-8').splitlines())
                # add the rst sourcode directive before output then...
                html_output_esc = ".. sourcecode:: html\n\n    "+html_output_esc+" \n "
                # ...process output as reStructuredText for HTML output area.
                html_output_esc = self.render_rst(html_output_esc)
            else:
                html_output = self.render_md(raw_input)
                # encode to iso-8859-1 to correct output. http://www.red-mercury.com/blog/eclectic-tech/python-unicode-fixing-utf-8-encoded-as-latin-1-iso-8859-1/
                html_output_esc = html_output.encode('iso-8859-1')
                # encode to utf-8, split on new lines, re-join to single-line http://stackoverflow.com/questions/2201633/replace-newlines-in-a-unicode-string
                html_output_esc = ''.join(unicode(html_output_esc, 'utf-8').splitlines())
                # add the rst sourcode directive before output then...
                html_output_esc = ".. sourcecode:: html\n\n    "+html_output_esc+" \n "
                # ...process output as reStructuredText for HTML output area.
                html_output_esc = self.render_rst(html_output_esc) 
        else: # default to rst if markup_type isn't defined
            html_output = u""
            html_output_esc = u""
        # / reStructuredText/markdown stuff
        
        
        # Of course if any of these values are created from user input, they need to be escaped appropriately.
        variables = { 'message':'Hello, Tornado!', 
                       'page_title': self.settings["page_title"], 'page_description': '', 
                       'page_author': 'The author of the page.', 'raw_input':raw_input, 'html_output':html_output, 'html_output_esc': html_output_esc, 'sourcecode_stylesheet': self.settings["sourcecode_stylesheet"], 'HTTPFUNCTION':'POST', 'markup_type': markup_type }

        # added the raw_input and html_output to the 
        content = self.render_template('hello_world.html', variables)
        self.write(content)

settings = {
    "page_title": u"A Good Start with Google App Engine: An Example Application -  Tornado-Jinja2-Docutils/reStructuredText-Pygments!",
    "templates": "views",
    "sourcecode_stylesheet": "default",
    "xsrf_cookies": False,
}
"""settings dictionary
The settings dictionary stores, of all things, settings, for the application. It's no joke! You can include your own entries such as the name of the application as you want it to be on the top of each page ("page_title" above) or tell Tornado to turn on or off the xsrf_cookies (among other things).

Using self.settings["page_title"] we can access the page_title entry of the settings dictionary from within your handlers."""




def main():
    """The Main Function, not to be confused with the MainHandler.
    
    This is the webapp version:
        application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    
    This is the tornado version:
        application = tornado.wsgi.WSGIApplication([ (r"/", MainHandler), ], **settings) 
    
    
    We also have to run it differently too:
        wsgiref.handlers.CGIHandler().run(application)        
    """
    
    application = tornado.wsgi.WSGIApplication([ (r"/", MainHandler), ], **settings)
    """ Set up a tornado WSGIApplication """
    
    # We have to run it differently too:
    wsgiref.handlers.CGIHandler().run(application)
    """ Use the wsgiref in the Python standard library to run the Tornado application. """



if __name__ == '__main__':
    main()
