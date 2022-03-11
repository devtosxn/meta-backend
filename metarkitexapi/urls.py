from django.urls import path

from . import views

urlpatterns = [
    path("add-email/", views.EmailViewSet.as_view({"post": "add_user_email"}), name="add email"),
]