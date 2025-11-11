from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import TemplateView
from django.db.models import Count
from core.models import Question, Tag

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

class IndexView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.session.get('is_authenticated', True)
        username = self.request.session.get('username', 'user') if is_authenticated else ''        
       
        questions = Question.objects.all().order_by('-created_at')
        page_obj = paginate(questions, self.request, 5)
        
        context.update({
            'questions': page_obj,
            'is_authenticated': is_authenticated,
            'username': username,
            'current_sort': 'new',
            'popular_tags': get_popular_tags()
        })
        return context

class HotView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.session.get('is_authenticated', True)
        username = self.request.session.get('username', 'user') if is_authenticated else ''
        
        
        questions = Question.objects.annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count', '-created_at')
        page_obj = paginate(questions, self.request, 5)
        
        context.update({
            'questions': page_obj,
            'is_authenticated': is_authenticated,
            'username': username,
            'current_sort': 'hot',
            'popular_tags': get_popular_tags()
        })
        return context

class TagView(TemplateView):
    template_name = 'core/tag.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.session.get('is_authenticated', True)
        username = self.request.session.get('username', 'user') if is_authenticated else ''
        tag_name = kwargs.get('tag_name')
        
        questions = Question.objects.filter(tags__title=tag_name).order_by('-created_at')
        page_obj = paginate(questions, self.request, 5)
        
        context.update({
            'questions': page_obj,
            'tag_name': tag_name,
            'is_authenticated': is_authenticated,
            'username': username,
            'popular_tags': get_popular_tags()
        })
        return context


class QuestionView(TemplateView):
    template_name = 'core/question.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.session.get('is_authenticated', True)
        username = self.request.session.get('username', 'user') if is_authenticated else ''
        question_id = kwargs.get('question_id')
        
        try:
            question_obj = Question.objects.get(id=question_id)
            answers = question_obj.answer_set.annotate(
                likes_count=Count('likes')
            ).order_by('-likes_count', '-created_at')
            page_obj = paginate(answers, self.request, 3)
            
            context.update({
                'question': question_obj,
                'answers': page_obj,
                'is_authenticated': is_authenticated,
                'username': username,
                'popular_tags': get_popular_tags()
            })
        except Question.DoesNotExist:
            pass
            
        return context
    
class LoginView(TemplateView):
    template_name = 'core/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'is_authenticated': self.request.session.get('is_authenticated', False),
            'username': '',
            'popular_tags': get_popular_tags()
        })
        return context

class SignupView(TemplateView):
    template_name = 'core/signup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'is_authenticated': self.request.session.get('is_authenticated', False),
            'username': '',
            'popular_tags': get_popular_tags()
        })
        return context

class AskView(TemplateView):
    template_name = 'core/ask.html'
    
    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.session.get('is_authenticated', True)
        if not is_authenticated:
            return redirect('signup')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.session.get('is_authenticated', True)
            
        context.update({
            'is_authenticated': is_authenticated,
            'username': self.request.session.get('username', 'user'),
            'popular_tags': get_popular_tags()
        })
        return context

class SettingsView(TemplateView):
    template_name = 'core/settings.html'
    
    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.session.get('is_authenticated', True)
        if not is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_authenticated = self.request.session.get('is_authenticated', True)
            
        context.update({
            'is_authenticated': is_authenticated,
            'username': self.request.session.get('username', 'user'),
            'popular_tags': get_popular_tags()
        })
        return context

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

def process_login(request):
    if request.method == 'POST':
        request.session['is_authenticated'] = True
        request.session['username'] = 'user'
        return redirect('index')
    return redirect('login')

def register_user(request):
    if request.method == 'POST':
        request.session['is_authenticated'] = True
        request.session['username'] = 'user'
        return redirect('index')
    return redirect('signup')

def logout_view(request):
    request.session['is_authenticated'] = False
    request.session['username'] = ''
    return redirect('index')