from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

handler500 = 'utils.views.server_error'

urlpatterns = patterns('')

# Debug/Development URLs
if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    )
# During development if you want to serve media just add the following
# setting to your local_settings.py and make sure your MEDIA_URL in your
# settings is a relative url like /static/
# SERVE_MEDIA = True
if hasattr(settings, 'SERVE_MEDIA'):
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {'document_root': '%s%s' % (settings.DJANGO_PROJECT_ROOT, settings.MEDIA_URL)}),
    )

# Admin Site
admin.autodiscover()

# Includes
urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
)

# Project Urls
urlpatterns += patterns('django.views.generic.simple',
    (r'^$', 'direct_to_template', {'template': 'index.html'}),
)
