from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('hot/', views.HotView.as_view(), name='hot'),
    path('tag/<str:tag_name>/', views.TagView.as_view(), name='tag'),
    path('question/<int:question_id>/', views.QuestionView.as_view(), name='question'),
    path('question/<int:question_id>/like/', views.like_question, name='like_question'),
    path('answer/<int:answer_id>/like/', views.like_answer, name='like_answer'),
    path('login/', views.AuthView.as_view(), name='login'),
    path('process-login/', views.process_login, name='process_login'), 
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('register/', views.register_user, name='register'),
    path('ask/', views.AskView.as_view(), name='ask'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('logout/', views.logout_view, name='logout'),
]