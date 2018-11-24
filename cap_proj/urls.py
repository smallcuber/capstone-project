from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from data.views import providers, scheduleview, patientovview, performanceview, PatientInfo, ProviderInfo, userLogin, userLogout, uploadModel

urlpatterns = [
    path(r'', admin.site.urls),
    path('admin/', admin.site.urls),
    path('providers/', providers, name='providers'),
    path('providers/<provider_scheduled>/', ProviderInfo.as_view(), name='provider_info'),
    path('schedule/', scheduleview, name='schedule'),
    path('patientov/', patientovview, name='patients'),
    path('patientov/<patient_id>/', PatientInfo.as_view(), name='patient_info'),
    path('performance/', performanceview, name='performance'),
    path('userlogin/', userLogin, name='login'),
    path('userlogout/', userLogout, name='logout'),
    path('modelupload/', uploadModel, name='modelupload'),
    path(r'data/', include('data.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
