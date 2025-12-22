from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.urls import swagger_like_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), 
]

urlpatterns += [
    path(
        'api/schema/likes/',
        SpectacularAPIView.as_view(patterns=swagger_like_patterns),
        name='schema-likes',
    ),
    path(
        'api/docs/likes/',
        SpectacularSwaggerView.as_view(url_name='schema-likes'),
        name='swagger-likes',
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)