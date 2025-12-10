"""
URL configuration for streamsmart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponse
from django.views.static import serve
from django.conf import settings
import os


def health_check(request):
    """Health check endpoint for Railway."""
    return JsonResponse({"status": "ok"})


def serve_frontend(request):
    """Serve the React frontend for all non-API routes."""
    index_path = os.path.join(settings.STATIC_ROOT, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HttpResponse(f.read(), content_type="text/html")
    return HttpResponse("Frontend not found", status=404)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/v1/summarizer/", include("summarizer.api_urls")),
    path("api/v1/watchparty/", include("watchparty.api_urls")),
]

# Serve frontend for all other routes (SPA catch-all)
# This must be last
urlpatterns += [
    re_path(r"^(?!api/|admin/|static/|ws/).*$", serve_frontend),
]
