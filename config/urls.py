from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import include, path

from apps.accounts.forms import PasswordChangeFormStyled


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(f"{settings.URL_PATH}/dashboard/")
    return redirect(f"{settings.URL_PATH}/about/")


urlpatterns = [
    path("", root_redirect),
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            form_class=PasswordChangeFormStyled,
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html",
        ),
        name="password_change_done",
    ),
    path("dashboard/", include("apps.dashboard.urls")),
    path("items/", include("apps.items.urls")),
    path("panel/", include("apps.accounts.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("about/", include("apps.dashboard.about_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
