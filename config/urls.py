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
