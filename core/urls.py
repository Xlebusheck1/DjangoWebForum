from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('hot/', views.HotView.as_view(), name='hot'),
    path('tag/<str:tag_name>/', views.TagView.as_view(), name='tag'),
    path('question/<int:question_id>/', views.QuestionView.as_view(), name='question'),    
    path('login/', views.AuthView.as_view(), name='login'),    
    path('signup/', views.SignupView.as_view(), name='signup'),    
    path('ask/', views.AskView.as_view(), name='ask'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/password/', views.PasswordChangeView.as_view(), name='change_password'),
    path("users/", views.UsersView.as_view(), name="users"),
    
    path("api/question/<int:question_id>/like/", views.QuestionLikeAPIView.as_view(), name="question_like_api"),
    path("api/answer/<int:answer_id>/like/", views.AnswerLikeAPIView.as_view(), name="answer_like_api"),
    path("api/answer/mark-correct/", views.MarkCorrectAnswerAPIView.as_view(), name="mark_correct_answer_api"),
    path("api/search-order/", views.search_order_api, name="search_order_api"),
    path("my-questions/", views.MyQuestionsView.as_view(), name="my_questions"),
]
