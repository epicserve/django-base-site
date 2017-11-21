from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

from apps.base.views import NameChange

handler500 = 'utils.views.server_error'

urlpatterns = []

# Debug/Development URLs
if settings.DEBUG is True:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    ]

# Includes
urlpatterns += [
    url(r'^admin/', include(admin.site.urls)),
]

# Project Urls
urlpatterns += [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='site_index'),
    url(r'^accounts/name/$', NameChange.as_view(), name='account_change_name'),
    url(r'^accounts/', include('allauth.urls')),
]
