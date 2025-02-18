from .forms import RegisterForm
from django.views import View
from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate

class Register(View):
    '''
        View responsible for registering the user.
    '''
    def get(self, request):
        register_form = RegisterForm()        
        return render(request, 'user_authentication/register_view.html', context = {'register' : register_form})
    
    def post(self, request): 
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            new_user = User.objects.create_user(username = username, password = password)
            login(request, new_user)
            return redirect('tools:add-mac')
    

class Login(View):
    '''
        View responsible for authenticating and logging the user in.
    '''
    def get(self, request):
        return render(request, 'user_authentication/login_view.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        potential_user = authenticate(username = username, password = password)
        if potential_user:
            login(request, potential_user)
            return redirect('tools:add-mac')
        else:
            messages.error(request, message = 'Incorrect account credentials!')
            return redirect('authentication:login')

class Logout(View):
    '''
        View responsible for logging the user out of the session.
    '''
    def get(self, request):
        logout(request)
        return redirect('authentication:login')
