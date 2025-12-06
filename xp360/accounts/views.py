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
    from core.models import Turma
    
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        senha = request.POST.get("password")
        turma_id = request.POST.get("turma")  # ← NOVO: captura turma selecionada

        try:
            turma = Turma.objects.get(id=turma_id) if turma_id else None
            
            Usuario.objects.create_user(
                username=username,
                email=email,
                password=senha,
                tipo="ALUNO",
                turma=turma  # ← NOVO: associa turma ao aluno
            )
            return redirect('login')
            
        except Turma.DoesNotExist:
            return render(request, "accounts/cadastro_aluno.html", {
                "erro": "Turma selecionada não existe",
                "turmas": Turma.objects.all()
            })
        except Exception as e:
            return render(request, "accounts/cadastro_aluno.html", {
                "erro": f"Erro ao criar conta: {e}",
                "turmas": Turma.objects.all()
            })

    # GET: exibe formulário com lista de turmas
    turmas = Turma.objects.all().order_by('serie')
    return render(request, "accounts/cadastro_aluno.html", {"turmas": turmas})


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
    
    # 🔥 NOVO: Atualizar streak ao acessar o dashboard
    request.user.atualizar_streak()
    
    # Busca missões do aluno
    missoes_aluno = MissaoAluno.objects.filter(aluno=request.user).order_by('-missao__data_criacao')
    
    # Calcula estatísticas
    total_missoes = missoes_aluno.count()
    concluidas = missoes_aluno.filter(concluida=True).count()
    pendentes = total_missoes - concluidas
    progresso = (concluidas / total_missoes * 100) if total_missoes > 0 else 0
    
    # Missões de hoje
    concluidas_hoje = missoes_aluno.filter(
        concluida=True,
        data_conclusao=timezone.now().date()
    ).count()
    
    context = {
        'missoes': missoes_aluno,
        'xp_total': request.user.xp_total,
        'nivel': request.user.nivel,
        'xp_proximo': request.user.xp_para_proximo_nivel(),
        'progresso_nivel': request.user.progresso_nivel(),
        'total_hoje': total_missoes,
        'concluidas_hoje': concluidas_hoje,
        'pendentes': pendentes,
        'progresso_dia': int(progresso),
        
        # 🔥 NOVO: Dados de streak
        'streak_atual': request.user.streak_atual,
        'melhor_streak': request.user.melhor_streak,
        'titulo_streak': request.user.get_titulo_streak(),
    }
    
    return render(request, 'accounts/dashboard_aluno.html', context)



@login_required
def detalhes_turma(request, turma_id):
    """View para ver detalhes de uma turma específica"""
    from core.models import Turma, MissaoAluno
    
    turma = Turma.objects.get(id=turma_id, professor=request.user)
    
    # ✅ CORREÇÃO: usar usuario_set ao invés de alunos
    alunos = turma.usuario_set.filter(tipo='ALUNO')
    
    missoes = turma.missao_set.all()
    
    # Estatísticas
    total_alunos = alunos.count()
    total_missoes = missoes.count()
    
    # Progresso dos alunos
    alunos_progresso = []
    for aluno in alunos:
        missoes_concluidas = MissaoAluno.objects.filter(
            aluno=aluno, 
            missao__turma=turma, 
            concluida=True
        ).count()
        
        progresso = (missoes_concluidas / total_missoes * 100) if total_missoes > 0 else 0
        
        alunos_progresso.append({
            'aluno': aluno,
            'missoes_concluidas': missoes_concluidas,
            'progresso': int(progresso),
            'xp_total': aluno.xp_total,
            'nivel': aluno.nivel,
        })
    
    # Ordena por XP (ranking)
    alunos_progresso.sort(key=lambda x: x['xp_total'], reverse=True)
    
    context = {
        'turma': turma,
        'alunos_progresso': alunos_progresso,
        'missoes': missoes,
        'total_alunos': total_alunos,
        'total_missoes': total_missoes,
    }
    
    return render(request, 'accounts/detalhes_turma.html', context)