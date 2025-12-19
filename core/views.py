from django.http import JsonResponse
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
User = get_user_model()

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

def search_order_api(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"order": []})

    user = request.user
    
    current_sort = request.GET.get("sort", "new")
    tag_name = request.GET.get("tag") 

    qs = Question.objects.all()

    if tag_name:
        qs = qs.filter(tags__name=tag_name)

    if current_sort == "hot":
        qs = qs.annotate(likes_count=Count("likes")).order_by("-likes_count", "-created_at")
    else:
        qs = qs.order_by("-created_at")
   
    qs = qs.filter(
        Q(title__icontains=q) |
        Q(detailed__icontains=q)
    )
   
    ids = list(qs.values_list("id", flat=True))

    return JsonResponse({"order": ids})

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

def get_popular_tags():    
    return Tag.objects.annotate(
        questions_count=Count('question')
    ).order_by('-questions_count')[:10]

def get_top_users(limit=5):
    users = list(User.objects.order_by("-rating", "id"))
    top = users[:limit]

    result = []
    for index, user in enumerate(top, start=1):
        current_rank = index
        old_rank = user.rank or current_rank
        diff = old_rank - current_rank 
        result.append((user, current_rank, diff))
    return result


@method_decorator(never_cache, name='dispatch')
@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        questions = (
            Question.objects
            .all()
            .order_by('-created_at')
            .annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef('pk'),
                        is_like=True,
                    )
                )
            )
        )
        page_obj = paginate(questions, self.request, 5)

        context.update({
            'questions': page_obj,
            'is_authenticated': user.is_authenticated,
            'username': user.username if user.is_authenticated else '',
            'current_sort': 'new',
            'popular_tags': Tag.objects.annotate(
                questions_count=Count('question')
            ).order_by('-questions_count')[:10],
            'top_users': get_top_users() 
        })
        return context


class HotView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        username = self.request.user.username if is_authenticated else ''

        user = self.request.user
        questions = (
            Question.objects
            .annotate(
                likes_count=Count('likes'),
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef('pk'),
                        is_like=True,
                    )
                )
            )
            .order_by('-likes_count', '-created_at')
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


class TagView(TemplateView):
    template_name = 'core/tag.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        username = self.request.user.username if is_authenticated else ''
        tag_name = kwargs.get('tag_name')

        user = self.request.user
        questions = (
            Question.objects
            .filter(tags__name=tag_name)
            .order_by('-created_at')
            .annotate(
                is_liked=Exists(
                    QuestionLike.objects.filter(
                        author=user,
                        question_id=OuterRef('pk'),
                        is_like=True,
                    )
                )
            )
        )
        page_obj = paginate(questions, self.request, 5)

        context.update({
            'questions': page_obj,
            'tag_name': tag_name,
            'is _authenticated': is_authenticated,
            'username': username,
            'popular_tags': get_popular_tags(),
            'top_users': get_top_users(),
        })
        return context


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

            context.update(
                {
                    "question": question_obj,
                    "answers": page_obj,
                    "answers_sort": sort,
                    "is_authenticated": is_authenticated,
                    "username": username,
                    "popular_tags": get_popular_tags(),
                    "answer_form": AnswerForm(),  
                }
            )
        except Question.DoesNotExist:
            pass

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        question_id = kwargs.get("question_id")
        question = get_object_or_404(Question, id=question_id)

        form = AnswerForm(request.POST)
        if form.is_valid():
            Answer.objects.create(
                question=question,
                author=request.user,
                answer_text=form.cleaned_data["answer_text"],
            )
            return redirect("question", question_id=question_id)
       
        context = self.get_context_data(question_id=question_id)
        context["answer_form"] = form
        return self.render_to_response(context)
    

@method_decorator(login_required, name='dispatch')
class AskView(TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'core/ask.html'
    
    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.user.is_authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.user.is_authenticated
        username = self.request.user.username if is_authenticated else ''    
        context['form'] = QuestionForm()        
        context['tags'] = Tag.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        form = QuestionForm(request.POST)
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
            return redirect('index')
        
        return render(request, self.template_name, {'form': form, 'tags': Tag.objects.all()})


@method_decorator(login_required, name='dispatch')
class PasswordChangeView(TemplateView):
    template_name = 'core/change_password.html'

    def get(self, request, *args, **kwargs):
        form = PasswordChangeForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = form.save(request.user)            
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён')
            return redirect('settings') 
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class SettingsView(TemplateView):
    template_name = 'core/settings.html'
    
    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.user.is_authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
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


class AuthView(TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'core/auth.html'

    def get_context_data(self, **kwargs):
        form = LoginForm()
        context = super(AuthView, self).get_context_data(**kwargs)
        context['form'] = form
        return context
    
    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            messages.add_message(request, messages.SUCCESS , "Успешная авторизация")
            return redirect('/')
        
        return render(request, template_name='core/auth.html', context={'form': form})


@login_required()
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/')


class SignupView(TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'core/signup.html'

    def get_context_data(self, **kwargs):
        form = SignupForm()
        context = super(SignupView, self).get_context_data(**kwargs)
        context['form'] = form
        return context
    
    def post(self, request, *args, **kwargs):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.add_message(request, messages.SUCCESS , "Успешная регистрация")
            return redirect('/')
        
        return render(request, template_name='core/signup.html', context={'form': form})


def like_question(request, question_id):
    if request.method == 'POST' and request.session.get('is_authenticated'):
        ...
        return redirect('question', question_id=question_id)
    return redirect('login')

def like_answer(request, answer_id):
    if request.method == 'POST' and request.session.get('is_authenticated'):
        ...
        return redirect('question', question_id=request.POST.get('question_id'))
    return redirect('login')


@method_decorator(login_required, name='dispatch')
class QuestionLikeAPIView(View):
    http_method_names = ['post']

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

        return JsonResponse({
            'success': True,
            'rating': question.rating,
        }, status=200)



@method_decorator(login_required, name="dispatch")
class AnswerLikeAPIView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        answer_id = request.POST.get("pk")
        is_like = request.POST.get("is_like", "true") == "true"

        answer = get_object_or_404(Answer, pk=answer_id)

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
        return JsonResponse({"success": True, "rating": answer.rating}, status=200)
    

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

        return JsonResponse({"success": True}, status=200)
    

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
        })
        return context
    

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