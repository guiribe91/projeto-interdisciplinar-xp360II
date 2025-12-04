from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("core/", include("core.urls")),  # <-- ESSA LINHA É OBRIGATÓRIA
    path("admin/", admin.site.urls),
]
