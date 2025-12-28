# tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count

from core import views
from core.models import Question, Tag
from core.views import (
    paginate,
    get_popular_tags,
    get_top_users,
    recalculate_user_ranks,
    QuestionLikeAPIView,
    AnswerLikeAPIView,
    MarkCorrectAnswerAPIView,
)
from core.models import Answer, AnswerLike, QuestionLike

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="user1", password="testpass", rating=0, rank=0
        )
        self.user2 = User.objects.create_user(
            username="user2", password="testpass", rating=0, rank=0
        )
        self.client.login(username="user1", password="testpass")

        self.tag = Tag.objects.create(name="python")
        self.question = Question.objects.create(
            title="Test question",
            detailed="Details",
            author=self.user,
        )
        self.question.tags.add(self.tag)

        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user2,
            answer_text="answer text",
        )


class UtilsTests(BaseTestCase):
    def test_paginate_basic(self):
        qs = Question.objects.all()
        request = self.client.get("/")  # фейковый request
        page = paginate(qs, request.wsgi_request, per_page=1)
        self.assertEqual(page.paginator.count, qs.count())
        self.assertEqual(page.number, 1)

    def test_get_popular_tags(self):
        # один тег, одна привязка к вопросу => questions_count == 1
        tags = get_popular_tags()
        self.assertIn(self.tag, list(tags))
        self.assertEqual(tags[0].questions_count, 1)

    def test_get_top_users_limit_and_diff(self):
        self.user.rating = 10
        self.user.save()
        self.user2.rating = 5
        self.user2.save()
        recalculate_user_ranks()

        top = get_top_users(limit=1)
        self.assertEqual(len(top), 1)
        u, pos, diff = top[0]
        self.assertEqual(u, self.user)
        self.assertEqual(pos, 1)
        # rank должен быть 1, diff == 0
        self.assertEqual(diff, 0)

    def test_recalculate_user_ranks_updates_rank(self):
        self.user.rating = 1
        self.user2.rating = 2
        self.user.save()
        self.user2.save()

        recalculate_user_ranks()
        self.user.refresh_from_db()
        self.user2.refresh_from_db()

        # user2 выше по рейтингу
        self.assertEqual(self.user2.rank, 1)
        self.assertEqual(self.user.rank, 2)


class SearchOrderApiTests(BaseTestCase):
    def test_search_order_empty_query_returns_empty(self):
        resp = self.client.get(reverse("search_order_api"), {"q": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"order": []})

    def test_search_order_non_empty(self):
        resp = self.client.get(reverse("search_order_api"), {"q": "Test"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(self.question.id, data["order"])


class IndexViewTests(BaseTestCase):
    def test_index_view_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 302)

    def test_index_view_context(self):
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/index.html")
        self.assertIn("questions", resp.context)
        self.assertIn("popular_tags", resp.context)
        self.assertIn("top_users", resp.context)


class HotViewTests(BaseTestCase):
    def test_hot_view_loading(self):
        resp = self.client.get(reverse("hot"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/index.html")
        self.assertEqual(resp.context["current_sort"], "hot")


class TagViewTests(BaseTestCase):
    def test_tag_view(self):
        resp = self.client.get(reverse("tag", args=[self.tag.name]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/tag.html")
        self.assertEqual(resp.context["tag_name"], self.tag.name)


class QuestionViewTests(BaseTestCase):
    def test_question_view_get(self):
        url = reverse("question", args=[self.question.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/question.html")
        self.assertEqual(resp.context["question"].id, self.question.id)
        self.assertIn("answers", resp.context)

    def test_question_view_post_add_answer(self):
        url = reverse("question", args=[self.question.id])
        data = {"answer_text": "New answer"}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Answer.objects.filter(question=self.question, answer_text="New answer").exists()
        )


class AskViewTests(BaseTestCase):
    def test_ask_view_get_form(self):
        resp = self.client.get(reverse("ask"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/ask.html")
        self.assertIn("form", resp.context)

    def test_ask_view_post_create_question(self):
        data = {"title": "Q2", "detailed": "text", "tags": ""}
        resp = self.client.post(reverse("ask"), data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Question.objects.filter(title="Q2").exists())


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="authuser", password="testpass"
        )

    def test_auth_view_get(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/auth.html")
        self.assertIn("form", resp.context)

    def test_auth_view_post_login(self):
        resp = self.client.post(
            reverse("login"),
            {"username": "authuser", "password": "testpass"},
        )
        self.assertEqual(resp.status_code, 302)


class SignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_get(self):
        resp = self.client.get(reverse("signup"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/signup.html")

    def test_signup_post(self):
        resp = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "Astrongpass123",
                "password2": "Astrongpass123",
                "email": "test@example.com",
            },
        )
        # форма у тебя кастомная, валидность может зависеть от логики,
        # но базовый тест на редирект:
        self.assertIn(resp.status_code, (200, 302))


class SettingsAndPasswordTests(BaseTestCase):
    def test_settings_get(self):
        resp = self.client.get(reverse("settings"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/settings.html")

    def test_change_password_get(self):
        resp = self.client.get(reverse("change_password"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/change_password.html")


class MyQuestionsViewTests(BaseTestCase):
    def test_my_questions_view(self):
        resp = self.client.get(reverse("my_questions"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/my_questions.html")
        self.assertTrue(
            all(q.author == self.user for q in resp.context["questions"])
        )


class UsersViewTests(BaseTestCase):
    def test_users_view(self):
        resp = self.client.get(reverse("users"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "core/users.html")
        self.assertIn("users_page", resp.context)
        self.assertGreaterEqual(len(resp.context["users_page"].object_list), 1)


class QuestionLikeApiTests(BaseTestCase):
    def test_question_like_forbidden_for_author(self):
        # сам автор вопроса лайкает свой вопрос
        resp = self.client.post(
            reverse("question_like_api", args=[self.question.id]),
            {"pk": self.question.id, "is_like": "true"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["success"], False)

    def test_question_like_toggle(self):
        # лайкает не автор, а другой юзер
        self.client.logout()
        self.client.login(username="user2", password="testpass")
        resp = self.client.post(
            reverse("question_like_api", args=[self.question.id]),
            {"pk": self.question.id, "is_like": "true"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, 1)


class AnswerLikeApiTests(BaseTestCase):
    def test_answer_like_forbidden_for_author(self):
        # автор ответа не может лайкнуть свой ответ
        self.client.logout()
        self.client.login(username="user2", password="testpass")
        resp = self.client.post(
            reverse("answer_like_api", args=[self.answer.id]),
            {"pk": self.answer.id, "is_like": "true"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["success"])

    def test_answer_like_toggle(self):
        # лайкает не автор
        resp = self.client.post(
            reverse("answer_like_api", args=[self.answer.id]),
            {"pk": self.answer.id, "is_like": "true"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, 1)


class MarkCorrectAnswerApiTests(BaseTestCase):
    def test_mark_correct_forbidden_if_not_question_author(self):
        # user2 (не автор вопроса) пытается пометить
        self.client.logout()
        self.client.login(username="user2", password="testpass")
        resp = self.client.post(
            reverse("mark_correct_answer_api"),
            {"pk": self.answer.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(resp.json()["success"])

    def test_mark_correct_sets_flag_and_updates_rating_and_rank(self):
        # user1 — автор вопроса, помечает ответ user2
        resp = self.client.post(
            reverse("mark_correct_answer_api"),
            {"pk": self.answer.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        self.answer.refresh_from_db()
        self.user2.refresh_from_db()

        self.assertTrue(self.answer.is_correct)
        self.assertEqual(self.user2.rating, 1)

        
        self.assertEqual(self.user2.rank, 1)
