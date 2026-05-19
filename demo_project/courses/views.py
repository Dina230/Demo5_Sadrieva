from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import RegisterForm, LoginForm, CourseRequestForm, ReviewForm
from .models import CourseRequest, Review


def is_admin26(user):
    """Проверка, является ли пользователь администратором"""
    return user.username == 'Admin26'


def register_view(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.first_name = form.cleaned_data['full_name']
            user.email = form.cleaned_data['email']
            user.last_name = form.cleaned_data['phone']  # сохраняем телефон
            user.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация успешно завершена.')
            return redirect('dashboard')
        else:
            # Выводим ошибки формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    """Авторизация пользователя"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Неверный логин или пароль')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')


@login_required
def dashboard(request):
    """Личный кабинет пользователя"""
    # Получаем заявки текущего пользователя
    requests_list = CourseRequest.objects.filter(user=request.user).order_by('-created_at')

    # Пагинация
    paginator = Paginator(requests_list, 5)
    page_number = request.GET.get('page')
    requests_page = paginator.get_page(page_number)

    # Получаем ID заявок, на которые уже есть отзывы
    reviews_exists = set(Review.objects.filter(user=request.user).values_list('request_id', flat=True))

    # Обработка отправки отзыва
    if request.method == 'POST' and 'review_text' in request.POST:
        req_id = request.POST.get('request_id')
        if req_id:
            try:
                req = CourseRequest.objects.get(id=req_id, user=request.user)

                # Проверяем, что статус "завершено"
                if req.status != 'completed':
                    messages.error(request, 'Отзыв можно оставить только после завершения курса')
                # Проверяем, что отзыв ещё не оставлен
                elif req.id in reviews_exists:
                    messages.error(request, 'Вы уже оставили отзыв на этот курс')
                else:
                    review_text = request.POST.get('review_text', '').strip()
                    if review_text:
                        Review.objects.create(
                            user=request.user,
                            request=req,
                            text=review_text
                        )
                        messages.success(request, 'Спасибо за отзыв!')
                        # Обновляем множество после добавления
                        reviews_exists.add(req.id)
                    else:
                        messages.error(request, 'Текст отзыва не может быть пустым')
            except CourseRequest.DoesNotExist:
                messages.error(request, 'Заявка не найдена')

        return redirect('dashboard')

    return render(request, 'dashboard.html', {
        'requests': requests_page,
        'reviews_exists': reviews_exists,
    })


@login_required
def create_request(request):
    """Страница создания новой заявки"""
    if request.method == 'POST':
        form = CourseRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, 'Заявка успешно создана и отправлена на согласование администратору')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CourseRequestForm()

    return render(request, 'create_request.html', {'form': form})


@login_required
@user_passes_test(is_admin26)
def admin_panel(request):
    """Панель администратора (только для Admin26)"""
    # Получаем все заявки
    requests_list = CourseRequest.objects.all().order_by('-created_at')

    # Фильтрация по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)

    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'user':
        requests_list = requests_list.order_by('user__username')
    elif sort_by == 'course':
        requests_list = requests_list.order_by('course_type')
    elif sort_by == 'date':
        requests_list = requests_list.order_by('start_date')
    elif sort_by == '-created_at':
        requests_list = requests_list.order_by('-created_at')
    else:
        requests_list = requests_list.order_by(sort_by)

    # Пагинация
    paginator = Paginator(requests_list, 5)
    page_number = request.GET.get('page')
    requests_page = paginator.get_page(page_number)

    # Обработка изменения статуса заявки
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        new_status = request.POST.get('status')

        if req_id and new_status:
            try:
                req = CourseRequest.objects.get(id=req_id)
                old_status = req.get_status_display()
                req.status = new_status
                req.save()
                messages.success(request, f'Заявка #{req.id} изменена: {old_status} → {req.get_status_display()}')
            except CourseRequest.DoesNotExist:
                messages.error(request, 'Заявка не найдена')

        return redirect('admin_panel')

    return render(request, 'admin_panel.html', {
        'requests': requests_page,
        'current_status': status_filter,
        'current_sort': sort_by,
    })