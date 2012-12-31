from django.conf.urls.defaults import *
from django.views.generic import TemplateView
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
urlpatterns += patterns('django.views.generic',
    (r'^$', TemplateView.as_view(template_name='index.html')),
)
