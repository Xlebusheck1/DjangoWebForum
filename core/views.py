import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import TemplateView
from core.models import Question, Tag
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from core.forms import LoginForm, QuestionForm, SignupForm, SettingsForm, PasswordChangeForm, AnswerForm
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views import View
from django.db.models import Count, Exists, OuterRef, Q
from .models import Answer, AnswerLike, QuestionLike
from .burst import BurstMixin
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db.models import BooleanField, ExpressionWrapper, Value, Exists, OuterRef
from core.caches import TagCache
from .centrifuge_client import CentrifugeClient
from django.views.decorators.csrf import csrf_exempt
from cent import Client
User = get_user_model()

# Пересчитывает ранги всех пользователей по их рейтингу.
def recalculate_user_ranks():
    users = User.objects.order_by("-rating", "id")
    current_rank = 1
    to_update = []
    for u in users:
        if u.rank != current_rank:
            u.rank = current_rank
            to_update.append(u)
        current_rank += 1
    if to_update:
        User.objects.bulk_update(to_update, ["rank"])


# Возвращает через API упорядоченный список ID вопросов, подходящих под строку поиска.
def search_order_api(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"order": []})

    qs = Question.objects.filter(
        Q(title__icontains=q) |
        Q(detailed__icontains=q)
    ).order_by("-created_at").values_list("id", flat=True)

    ids = list(qs)

    return JsonResponse({"order": ids})


# Универсальная функция пагинации для списков объектов.
def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    page = request.GET.get('page', 1)
    
    try:
        objects_page = paginator.page(page)
    except PageNotAnInteger:
        objects_page = paginator.page(1)
    except EmptyPage:
        objects_page = paginator.page(paginator.num_pages)
    
    return objects_page


# Возвращает самые популярные теги по количеству связанных вопросов.
def get_popular_tags():
    tags_data = TagCache.get_items()
    ids = [t["id"] for t in tags_data]
    qs = (Tag.objects
          .filter(id__in=ids)
          .annotate(questions_count=Count("question"))
          .order_by("-questions_count"))[:10]
    return qs

# Возвращает список топ‑пользователей с их текущим рангом и изменением позиции.


TOP_USERS_CACHE_KEY = "top_users"
TOP_USERS_TIMEOUT = 60 
def get_top_users(limit=5):
    cache_key = f"{TOP_USERS_CACHE_KEY}:{limit}"
    data = cache.get(cache_key)
    if data is not None:
        return data

    users = list(User.objects.order_by("-rating", "id"))
    top = users[:limit]

    result = []
    for index, user in enumerate(top, start=1):
        current_rank = index
        old_rank = user.rank or current_rank
        diff = old_rank - current_rank
        result.append((user, current_rank, diff))

    cache.set(cache_key, result, TOP_USERS_TIMEOUT)
    return result

# Главная страница с лентой новых вопросов.
@method_decorator(never_cache, name='dispatch')
class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        base_qs = Question.objects.all().order_by('-created_at')

        if user.is_authenticated:
            questions = base_qs.annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef('pk'),
                        is_like=True,
                    )
                )
            )
        else:
            questions = base_qs.annotate(
                is_liked=ExpressionWrapper(
                    Value(False),
                    output_field=BooleanField(),
                )
            )

        page_obj = paginate(questions, self.request, 5)

        context.update({
            'questions': page_obj,
            'is_authenticated': user.is_authenticated,
            'username': user.username if user.is_authenticated else '',
            'current_sort': 'new',
            'popular_tags': get_popular_tags(),
            'top_users': get_top_users(),
        })
        return context


# Страница с «горячими» вопросами, отсортированными по лайкам.
class HotView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_authenticated = user.is_authenticated
        username = user.username if is_authenticated else ''

        base_qs = Question.objects.annotate(
            likes_count=Count('likes'),
        ).order_by('-likes_count', '-created_at')

        if user.is_authenticated:
            questions = base_qs.annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef('pk'),
                        is_like=True,
                    )
                )
            )
        else:
            questions = base_qs.annotate(
                is_liked=ExpressionWrapper(
                    Value(False),
                    output_field=BooleanField(),
                )
            )

        page_obj = paginate(questions, self.request, 5)

        context.update({
            'questions': page_obj,
            'is_authenticated': is_authenticated,
            'username': username,
            'current_sort': 'hot',
            'popular_tags': get_popular_tags(),
            'top_users': get_top_users(),
        })
        return context


# Страница списка вопросов по конкретному тегу.
class TagView(TemplateView):
    template_name = 'core/tag.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_authenticated = user.is_authenticated
        username = user.username if is_authenticated else ''
        tag_name = kwargs.get('tag_name')

        base_qs = (Question.objects
                   .filter(tags__name=tag_name)
                   .order_by('-created_at'))

        if user.is_authenticated:
            questions = base_qs.annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef('pk'),
                        is_like=True,
                    )
                )
            )
        else:
            questions = base_qs.annotate(
                is_liked=ExpressionWrapper(
                    Value(False),
                    output_field=BooleanField(),
                )
            )

        page_obj = paginate(questions, self.request, 5)

        context.update({
            'questions': page_obj,
            'tag_name': tag_name,
            'is_authenticated': is_authenticated,
            'username': username,
            'popular_tags': get_popular_tags(),
            'top_users': get_top_users(),
        })
        return context


# Страница отдельного вопроса с ответами и формой добавления ответа.
class QuestionView(TemplateView):
    template_name = "core/question.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        username = self.request.user.username if is_authenticated else ""
        question_id = kwargs.get("question_id")

        try:
            question_qs = Question.objects.annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=self.request.user,
                        question_id=OuterRef("pk"),
                        is_like=True,
                    )
                )
            )
            question_obj = question_qs.get(id=question_id)

            sort = self.request.GET.get("sort", "best")
            base_qs = question_obj.answer_set.annotate(
                likes_count=Count("likes"),
                is_liked=Exists(
                    AnswerLike.objects.filter(
                        author=self.request.user,
                        answer_id=OuterRef("pk"),
                        is_like=True,
                    )
                ),
            )

            if sort == "new":
                answers = base_qs.order_by("-is_correct", "-created_at")
            else:
                answers = base_qs.order_by("-is_correct", "-likes_count", "-created_at")

            page_obj = paginate(answers, self.request, 3)
            
            centrifuge_data = {}
            if is_authenticated:
                from .centrifuge_client import CentrifugeClient
                centrifuge = CentrifugeClient()
                
                centrifuge_data = {
                    "centrifuge_ws_url": "ws://devguru.local/connection/websocket",
                    "centrifuge_connection_token": centrifuge.generate_connection_token(self.request.user),
                    "centrifuge_question_channel": f"questions:question_{question_id}",
                    "centrifuge_question_token": centrifuge.generate_token(
                        self.request.user.id, 
                        f"questions:question_{question_id}"
                    ),
                    "centrifuge_likes_channel": f"likes:question_{question_id}",
                    "centrifuge_likes_token": centrifuge.generate_token(
                        self.request.user.id,
                        f"likes:question_{question_id}"
                    ),
                }

            context.update(
                {
                    "question": question_obj,
                    "answers": page_obj,
                    "answers_sort": sort,
                    "is_authenticated": is_authenticated,
                    "username": username,
                    "popular_tags": get_popular_tags(),
                    "answer_form": AnswerForm(),
                    **centrifuge_data, 
                }
            )
        except Question.DoesNotExist:
            pass

        return context

    # Обрабатывает отправку формы с новым ответом на вопрос.
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        question_id = kwargs.get("question_id")
        question = get_object_or_404(Question, id=question_id)

        form = AnswerForm(request.POST)
        if form.is_valid():           
            answer = Answer.objects.create(
                question=question,
                author=request.user,
                answer_text=form.cleaned_data["answer_text"],
            )            
           
            from .centrifuge_client import CentrifugeClient
            centrifuge = CentrifugeClient()            
           
            answer_data = {
                "id": answer.id,
                "author": {
                    "id": answer.author.id,
                    "username": answer.author.username,
                    "avatar_url": answer.author.avatar.url if answer.author.avatar else None,
                },
                "answer_text": answer.answer_text,
                "rating": answer.rating,
                "is_correct": answer.is_correct,
                "created_at": answer.created_at.isoformat(),
                "question_id": question_id,
            }            
           
            centrifuge.publish_new_answer(question_id, answer_data)
            
            return redirect("question", question_id=question_id)
       
        context = self.get_context_data(question_id=question_id)
        context["answer_form"] = form
        return self.render_to_response(context)
    

ASK_FORM_SESSION_KEY = "ask_form_data"

@method_decorator(login_required, name='dispatch')
class AskView(BurstMixin, TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'core/ask.html'
    burst_key = 'ask'
    limits = {'minute': 10}

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        username = self.request.user.username if is_authenticated else ''
        data = self.request.session.get(ASK_FORM_SESSION_KEY)
        form = QuestionForm(initial=data) if data else QuestionForm()
        context.update({
            'form': form,
            'tags': Tag.objects.all(),
            'popular_tags': get_popular_tags(),
            'top_users': get_top_users(),
            'is_authenticated': is_authenticated,
            'username': username,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = QuestionForm(request.POST)
        request.session[ASK_FORM_SESSION_KEY] = request.POST.dict()
        if form.is_valid():
            title = form.cleaned_data['title']
            detailed = form.cleaned_data['detailed']
            question = Question.objects.create(
                title=title,
                detailed=detailed,
                author=request.user
            )
            tag_ids = request.POST.get('tags', '')
            tag_ids = [int(t) for t in tag_ids.split(',') if t.isdigit()]
            question.tags.set(tag_ids)
            request.session.pop(ASK_FORM_SESSION_KEY, None)
            return redirect('index')
        return render(request, self.template_name, {'form': form, 'tags': Tag.objects.all()})

# Страница смены пароля пользователя.
@method_decorator(login_required, name='dispatch')
class PasswordChangeView(TemplateView):
    template_name = 'core/change_password.html'

    def get(self, request, *args, **kwargs):
        form = PasswordChangeForm()
        return render(request, self.template_name, {'form': form})

    # Обрабатывает POST‑запрос на смену пароля.
    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = form.save(request.user)            
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён')
            return redirect('settings') 
        return render(request, self.template_name, {'form': form})


# Страница настроек профиля пользователя.
@method_decorator(login_required, name='dispatch')
class SettingsView(TemplateView):
    template_name = 'core/settings.html'
    
    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.user.is_authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
    # Обрабатывает сохранение настроек профиля.
    def post(self, request, *args, **kwargs):
        form = SettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('index') 
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        username = self.request.user.username if is_authenticated else ''
        context.update({
            'is_authenticated': is_authenticated,
            'username': username,
            'popular_tags': get_popular_tags()
        })
        context['form'] = SettingsForm(instance=self.request.user)
        return context


# Страница авторизации (логин пользователя).
@method_decorator(cache_page(60 * 5), name="get")
class AuthView(TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'core/auth.html'

    def get_context_data(self, **kwargs):
        form = LoginForm()
        context = super(AuthView, self).get_context_data(**kwargs)
        context['form'] = form
        return context
    
    # Обрабатывает отправку формы логина.
    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            messages.add_message(request, messages.SUCCESS , "Успешная авторизация")
            return redirect('/')
        
        return render(request, template_name='core/auth.html', context={'form': form})


# Обрабатывает разлогинивание пользователя и редирект на главную.
@login_required()
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/')
    

# Страница регистрации нового пользователя.
@method_decorator(cache_page(60 * 5), name="get")
class SignupView(TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'core/signup.html'

    def get_context_data(self, **kwargs):
        form = SignupForm()
        context = super(SignupView, self).get_context_data(**kwargs)
        context['form'] = form
        return context
    
    # Обрабатывает отправку формы регистрации.
    def post(self, request, *args, **kwargs):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.add_message(request, messages.SUCCESS , "Успешная регистрация")
            return redirect('/')
        
        return render(request, template_name='core/signup.html', context={'form': form})


# API‑эндпоинт для лайка/анлайка вопроса.
@method_decorator(login_required, name='dispatch')
class QuestionLikeAPIView(View):
    def post(self, request, *args, **kwargs):        
        question_id = request.POST.get('pk')        
        is_like = request.POST.get('is_like', 'true') == 'true'
        question = get_object_or_404(Question, pk=question_id)

        if question.author == request.user:
            return JsonResponse({
                'success': False,
                'error': 'Вы являетесь автором вопроса',
            }, status=400)

        like = QuestionLike.objects.filter(
            author=request.user,
            question_id=question_id
        ).first()

        if is_like:
            if not like:
                QuestionLike.objects.create(
                    author=request.user,
                    question=question,
                    is_like=True
                )
                question.rating += 1
        else:
            if like:
                like.delete()
                question.rating -= 1

        question.save(update_fields=['rating', 'updated_at'])
        
        # Используйте CentrifugeClient вместо get_centrifuge_client()
        from .centrifuge_client import CentrifugeClient
        centrifuge = CentrifugeClient()
        centrifuge.publish_like_update(question_id, {
            "type": "question_like",
            "question_id": question_id,
            "rating": question.rating,
            "user_id": request.user.id,
            "is_like": is_like
        })

        return JsonResponse({
            'success': True,
            'rating': question.rating,
        }, status=200)


# API‑эндпоинт для лайка/анлайка ответа.
@method_decorator(login_required, name="dispatch")
class AnswerLikeAPIView(View):
    def post(self, request, *args, **kwargs):
        answer_id = request.POST.get("pk")
        is_like = request.POST.get("is_like", "true") == "true"
        answer = get_object_or_404(Answer, pk=answer_id)
        question_id = answer.question.id

        if answer.author == request.user:
            return JsonResponse({"success": False, "error": "Нельзя лайкать свой ответ"}, status=400)

        like = AnswerLike.objects.filter(
            author=request.user,
            answer_id=answer_id,
            is_like=True,
        ).first()

        if is_like:
            if not like:
                AnswerLike.objects.create(author=request.user, answer=answer, is_like=True)
                answer.rating += 1
        else:
            if like:
                like.delete()
                answer.rating -= 1

        answer.save(update_fields=["rating", "updated_at"])
        
        # Используйте CentrifugeClient вместо get_centrifuge_client()
        from .centrifuge_client import CentrifugeClient
        centrifuge = CentrifugeClient()
        centrifuge.publish_like_update(question_id, {
            "type": "answer_like",
            "answer_id": answer_id,
            "question_id": question_id,
            "rating": answer.rating,
            "user_id": request.user.id,
            "is_like": is_like
        })
        
        return JsonResponse({"success": True, "rating": answer.rating}, status=200)
    

# API‑эндпоинт для пометки ответа как правильного.
@method_decorator(login_required, name="dispatch")
class MarkCorrectAnswerAPIView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        answer_id = request.POST.get("pk")
        answer = get_object_or_404(Answer, pk=answer_id)
        question = answer.question
        
        if question.author != request.user:
            return JsonResponse(
                {"success": False, "error": "Нет прав"},
                status=403,
            )
       
        previous_correct = Answer.objects.filter(
            question=question,
            is_correct=True,
        ).exclude(pk=answer.pk).first()
    
        Answer.objects.filter(question=question, is_correct=True).update(is_correct=False)
        
        if previous_correct:
            prev_author = previous_correct.author
            if prev_author.rating > 0:
                prev_author.rating -= 1
                prev_author.save(update_fields=["rating"])
        
        answer.is_correct = True
        answer.save(update_fields=["is_correct", "updated_at"])
        
        ans_author = answer.author
        ans_author.rating += 1
        ans_author.save(update_fields=["rating"])
        
        recalculate_user_ranks()
      
        from .centrifuge_client import CentrifugeClient
        centrifuge = CentrifugeClient()
        centrifuge.publish_like_update(question.id, {
            "type": "correct_answer",
            "answer_id": answer_id,
            "question_id": question.id,
            "user_id": answer.author.id,
        })

        return JsonResponse({"success": True}, status=200)
    

# Страница со списком вопросов текущего пользователя.
@method_decorator(login_required, name="dispatch")
class MyQuestionsView(TemplateView):
    template_name = "core/my_questions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        questions = (
            Question.objects
            .filter(author=user)
            .annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef("pk"),
                        is_like=True,
                    )
                )
            )
            .order_by("-created_at")
        )

        page_obj = paginate(questions, self.request, 5)

        context.update({
            "questions": page_obj,
            "is_authenticated": True,
            "username": user.username,
            "current_sort": "my",
            "popular_tags": get_popular_tags(),
            "top_users": get_top_users(), 
        })
        return context    


# Страница со списком всех пользователей и их рейтингами.
class UsersView(TemplateView):
    template_name = "core/users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        users_qs = User.objects.order_by("-rating", "id")
        users_list = list(users_qs)
      
        rows = []
        for index, user in enumerate(users_list, start=1):
            current_rank = index
            old_rank = user.rank or current_rank
            diff = old_rank - current_rank
            rows.append((user, current_rank, diff))

        paginator = Paginator(rows, 20)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context["users_page"] = page_obj
        return context
