from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.survey_list, name="survey_list"),
    path("submit/", views.submit_survey, name="submit_survey"),
    path("survey/<int:entry_id>/", views.survey_view, name="survey"),
]
