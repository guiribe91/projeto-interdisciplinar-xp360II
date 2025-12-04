from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Usuario
from core.models import MissaoAluno, Missao
from datetime import date

# ---------------------------------------------------------
# LOGIN / LOGOUT
# ---------------------------------------------------------

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("password")

        user = authenticate(request, username=username, password=senha)
        if user:
            login(request, user)

            # Redirecionamento por tipo
            if user.tipo == 'ALUNO':
                return redirect('dashboard_aluno')
            elif user.tipo == 'PROFESSOR':
                return redirect('dashboard_professor')

        else:
            return render(request, "accounts/login.html", {"erro": "Credenciais inválidas"})

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------------------------------------------------
# CADASTRO
# ---------------------------------------------------------

def cadastro_aluno(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        senha = request.POST.get("password")

        Usuario.objects.create_user(
            username=username,
            email=email,
            password=senha,
            tipo="ALUNO"
        )
        return redirect('login')

    return render(request, "accounts/cadastro_aluno.html")


def cadastro_professor(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        senha = request.POST.get("password")

        Usuario.objects.create_user(
            username=username,
            email=email,
            password=senha,
            tipo="PROFESSOR"
        )
        return redirect('login')

    return render(request, "accounts/cadastro_professor.html")


# ---------------------------------------------------------
# DASHBOARD PROFESSOR
# ---------------------------------------------------------

@login_required
def dashboard_professor(request):
    turmas = request.user.turmas.all()
    return render(request, "accounts/dashboard_professor.html", {"turmas": turmas})

# ---------------------------------------------------------
# DASHBOARD ALUNO
# ---------------------------------------------------------

@login_required
def dashboard_aluno(request):
    from core.models import MissaoAluno
    
    # Busca missões do aluno
    missoes_aluno = MissaoAluno.objects.filter(aluno=request.user).order_by('-missao__data_criacao')
    
    # Calcula estatísticas
    total_missoes = missoes_aluno.count()
    concluidas = missoes_aluno.filter(concluida=True).count()
    pendentes = total_missoes - concluidas
    progresso = (concluidas / total_missoes * 100) if total_missoes > 0 else 0
    
    context = {
        'missoes': missoes_aluno,
        'xp_total': request.user.xp_total,
        'nivel': request.user.nivel,
        'xp_proximo': request.user.xp_para_proximo_nivel(),
        'total_hoje': total_missoes,
        'concluidas_hoje': concluidas,
        'pendentes': pendentes,
        'progresso_dia': int(progresso),
    }
    
    return render(request, 'accounts/dashboard_aluno.html', context)