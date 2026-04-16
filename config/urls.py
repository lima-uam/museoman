from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", include("apps.dashboard.urls")),
    path("items/", include("apps.items.urls")),
    path("panel/", include("apps.accounts.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("about/", include("apps.dashboard.about_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
