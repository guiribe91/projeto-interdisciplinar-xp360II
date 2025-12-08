from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.generic import TemplateView  # 🆕 NOVO
from .models import Usuario
from core.models import MissaoAluno, Missao, Turma, Disciplina
from datetime import date
import json

# ---------------------------------------------------------
# 🆕 NOVAS VIEWS - PÁGINAS LEGAIS (LGPD)
# ---------------------------------------------------------

class PoliticaPrivacidadeView(TemplateView):
    template_name = 'accounts/politica_privacidade.html'

class TermosUsoView(TemplateView):
    template_name = 'accounts/termos_uso.html'


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
    """View para cadastro de aluno com múltiplas turmas"""
    
    if request.method == 'POST':
        try:
            # Dados do formulário
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            turmas_ids = request.POST.getlist('turmas')
            aceito_termos = request.POST.get('aceito_termos')  # 🆕 NOVO
            
            # 🆕 NOVO: Validar aceite dos termos
            if not aceito_termos:
                return render(request, 'accounts/cadastro_aluno.html', {
                    'turmas': Turma.objects.all().order_by('serie', 'nome'),
                    'erro': 'Você deve aceitar os Termos de Uso e a Política de Privacidade para se cadastrar.'
                })
            
            # Validações básicas
            if not username or not email or not password:
                return render(request, 'accounts/cadastro_aluno.html', {
                    'turmas': Turma.objects.all().order_by('serie', 'nome'),
                    'erro': 'Por favor, preencha todos os campos obrigatórios.'
                })
            
            if not turmas_ids:
                return render(request, 'accounts/cadastro_aluno.html', {
                    'turmas': Turma.objects.all().order_by('serie', 'nome'),
                    'erro': 'Por favor, selecione pelo menos uma turma.'
                })
            
            # Verificar se usuário já existe
            if Usuario.objects.filter(username=username).exists():
                return render(request, 'accounts/cadastro_aluno.html', {
                    'turmas': Turma.objects.all().order_by('serie', 'nome'),
                    'erro': 'Este nome de usuário já está em uso.'
                })
            
            if Usuario.objects.filter(email=email).exists():
                return render(request, 'accounts/cadastro_aluno.html', {
                    'turmas': Turma.objects.all().order_by('serie', 'nome'),
                    'erro': 'Este e-mail já está cadastrado.'
                })
            
            # Criar usuário
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                tipo='ALUNO'
            )
            
            # 🆕 NOVO: Registrar aceite dos termos (LGPD)
            usuario.aceitou_termos = True
            usuario.data_aceite_termos = timezone.now()
            
            # Capturar IP do usuário
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                usuario.ip_aceite_termos = x_forwarded_for.split(',')[0]
            else:
                usuario.ip_aceite_termos = request.META.get('REMOTE_ADDR')
            
            # Associar turmas
            turmas = Turma.objects.filter(id__in=turmas_ids)
            usuario.turmas_aluno.set(turmas)
            
            # Salvar
            usuario.save()
            
            # Mensagem de sucesso
            messages.success(
                request, 
                f'Conta criada com sucesso! Você foi matriculado em {turmas.count()} turma(s). Faça login para começar.'
            )
            
            return redirect('login')
            
        except Exception as e:
            return render(request, 'accounts/cadastro_aluno.html', {
                'turmas': Turma.objects.all().order_by('serie', 'nome'),
                'erro': f'Erro ao criar conta: {str(e)}'
            })
    
    # GET - Mostrar formulário
    context = {
        'turmas': Turma.objects.all().order_by('serie', 'nome')
    }
    
    return render(request, 'accounts/cadastro_aluno.html', context)


def cadastro_professor(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        senha = request.POST.get("password")
        aceito_termos = request.POST.get('aceito_termos')  # 🆕 NOVO
        
        # 🆕 NOVO: Validar aceite dos termos
        if not aceito_termos:
            return render(request, "accounts/cadastro_professor.html", {
                'erro': 'Você deve aceitar os Termos de Uso e a Política de Privacidade para se cadastrar.'
            })

        # Criar usuário
        usuario = Usuario.objects.create_user(
            username=username,
            email=email,
            password=senha,
            tipo="PROFESSOR"
        )
        
        # 🆕 NOVO: Registrar aceite dos termos (LGPD)
        usuario.aceitou_termos = True
        usuario.data_aceite_termos = timezone.now()
        
        # Capturar IP do usuário
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            usuario.ip_aceite_termos = x_forwarded_for.split(',')[0]
        else:
            usuario.ip_aceite_termos = request.META.get('REMOTE_ADDR')
        
        usuario.save()
        
        messages.success(request, 'Conta de professor criada com sucesso! Faça login para começar.')
        return redirect('login')

    return render(request, "accounts/cadastro_professor.html")


# ---------------------------------------------------------
# DASHBOARD PROFESSOR
# ---------------------------------------------------------

@login_required
def dashboard_professor(request):
    # Buscar turmas do professor usando o novo related_name
    turmas = request.user.turmas_professor.all()
    
    # Buscar todas as disciplinas
    disciplinas = Disciplina.objects.all().order_by('nome')
    
    # Buscar missões criadas pelo professor
    missoes = Missao.objects.filter(turma__in=turmas)
    
    # Calcular total de alunos
    total_alunos = 0
    for turma in turmas:
        total_alunos += turma.alunos.count()
    
    context = {
        'turmas': turmas,
        'disciplinas': disciplinas,
        'missoes': missoes,
        'total_alunos': total_alunos,
    }
    
    return render(request, "accounts/dashboard_professor.html", context)


# ---------------------------------------------------------
# GERENCIAR TURMAS
# ---------------------------------------------------------

@login_required
def criar_turma(request):
    """
    View para criar uma nova turma.
    Apenas professores podem criar turmas.
    """
    if request.method == 'POST':
        # Verificar se o usuário é professor
        if request.user.tipo != 'PROFESSOR':
            messages.error(request, '❌ Apenas professores podem criar turmas!')
            return redirect('dashboard_professor')
        
        # Pegar dados do formulário
        nome = request.POST.get('nome')
        serie = request.POST.get('serie')
        ano_letivo = request.POST.get('ano_letivo')
        
        # Validar dados
        if not nome or not serie or not ano_letivo:
            messages.error(request, '❌ Preencha todos os campos obrigatórios!')
            return redirect('dashboard_professor')
        
        try:
            # Criar a turma
            turma = Turma.objects.create(
                nome=nome,
                serie=serie,
                ano_letivo=int(ano_letivo),
                professor=request.user
            )
            
            messages.success(request, f'✅ Turma "{nome}" criada com sucesso!')
            return redirect('dashboard_professor')
            
        except Exception as e:
            messages.error(request, f'❌ Erro ao criar turma: {str(e)}')
            return redirect('dashboard_professor')
    
    return redirect('dashboard_professor')


@login_required
def editar_turma(request, turma_id):
    """
    View para editar uma turma existente.
    Apenas o professor que criou a turma pode editá-la.
    """
    turma = get_object_or_404(Turma, id=turma_id)
    
    # Verificar se o usuário é o professor da turma
    if turma.professor != request.user:
        messages.error(request, '❌ Você não tem permissão para editar esta turma!')
        return redirect('dashboard_professor')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        serie = request.POST.get('serie')
        ano_letivo = request.POST.get('ano_letivo')
        
        if not nome or not serie or not ano_letivo:
            messages.error(request, '❌ Preencha todos os campos!')
            return redirect('dashboard_professor')
        
        try:
            turma.nome = nome
            turma.serie = serie
            turma.ano_letivo = int(ano_letivo)
            turma.save()
            
            messages.success(request, f'✅ Turma "{nome}" atualizada com sucesso!')
            return redirect('dashboard_professor')
            
        except Exception as e:
            messages.error(request, f'❌ Erro ao atualizar turma: {str(e)}')
            return redirect('dashboard_professor')
    
    return redirect('dashboard_professor')


@login_required
def deletar_turma(request, turma_id):
    """
    View para deletar uma turma (opcional).
    """
    turma = get_object_or_404(Turma, id=turma_id)
    
    if turma.professor != request.user:
        messages.error(request, '❌ Você não tem permissão para deletar esta turma!')
        return redirect('dashboard_professor')
    
    if request.method == 'POST':
        nome_turma = turma.nome
        turma.delete()
        messages.success(request, f'✅ Turma "{nome_turma}" deletada com sucesso!')
    
    return redirect('dashboard_professor')


# ---------------------------------------------------------
# DASHBOARD ALUNO
# ---------------------------------------------------------

@login_required
def dashboard_aluno(request):
    # Atualizar streak ao acessar o dashboard
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
    
    # Pegar notificações da sessão
    badges_novas = request.session.pop('badges_novas', None)
    nivel_novo = request.session.pop('nivel_novo', None)
    streak_info = request.session.pop('streak_info', None)
    
    # Converter streak_info de JSON string para dict se existir
    if streak_info:
        try:
            streak_info = json.loads(streak_info)
        except:
            streak_info = None
    
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
        
        # Dados de streak
        'streak_atual': request.user.streak_atual,
        'melhor_streak': request.user.melhor_streak,
        'titulo_streak': request.user.get_titulo_streak(),
        
        # Dados para notificações
        'badges_novas': json.dumps(badges_novas) if badges_novas else '[]',
        'nivel_novo': nivel_novo,
        'streak_info': json.dumps(streak_info) if streak_info else 'null',
    }
    
    return render(request, 'accounts/dashboard_aluno.html', context)


# ---------------------------------------------------------
# DETALHES DA TURMA
# ---------------------------------------------------------

@login_required
def detalhes_turma(request, turma_id):
    """View para ver detalhes de uma turma específica"""
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    
    # Buscar alunos da turma usando o related_name 'alunos'
    alunos = turma.alunos.all()
    
    # Buscar missões da turma
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


# ---------------------------------------------------------
# RANKING
# ---------------------------------------------------------

@login_required
def ranking(request):
    # Buscar todas as turmas do aluno
    turmas_aluno = request.user.turmas_aluno.all()
    
    if turmas_aluno.exists():
        # Pegar alunos de todas as turmas do usuário
        alunos = Usuario.objects.filter(
            tipo='ALUNO',
            turmas_aluno__in=turmas_aluno
        ).distinct().order_by('-xp_total')[:10]
        
        # Calcular posição do usuário atual
        posicao_usuario = Usuario.objects.filter(
            tipo='ALUNO',
            turmas_aluno__in=turmas_aluno,
            xp_total__gt=request.user.xp_total
        ).distinct().count() + 1
    else:
        alunos = []
        posicao_usuario = 0
    
    context = {
        'alunos': alunos,
        'posicao_usuario': posicao_usuario,
    }
    
    return render(request, 'accounts/ranking.html', context)


# ---------------------------------------------------------
# CONQUISTAS (BADGES)
# ---------------------------------------------------------

@login_required
def conquistas(request):
    from .models import BadgeUsuario, Badge
    from .badges import get_progresso_badges
    
    # Badges conquistadas
    badges_conquistadas = BadgeUsuario.objects.filter(
        usuario=request.user
    ).select_related('badge')
    
    # Todas as badges
    todas_badges = Badge.objects.all()
    
    # IDs das conquistadas
    conquistadas_ids = set(badges_conquistadas.values_list('badge_id', flat=True))
    
    # Progresso das pendentes
    progresso_badges = get_progresso_badges(request.user)
    
    context = {
        'titulo': 'Minhas Conquistas',
        'badges_conquistadas': badges_conquistadas,
        'total_badges': todas_badges.count(),
        'total_conquistadas': badges_conquistadas.count(),
        'progresso_badges': progresso_badges,
        'conquistadas_ids': conquistadas_ids,
    }
    
    return render(request, 'accounts/conquistas.html', context)
