from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from data.views import providers, scheduleview, patientovview

urlpatterns = [
    path('admin/', admin.site.urls),
    path('employees/', providers, name='this_view'),
    path('schedule/', scheduleview, name='schedule'),
    path('patientov/', patientovview, name='patients'),
    path(r'data/', include('data.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
