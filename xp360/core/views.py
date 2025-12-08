from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from django.http import JsonResponse
from django.db.models import Q

# =============================
# CRIAR MISSÃO
# =============================
@login_required
def criar_missao(request):
    if request.method == "POST":
        from .models import Turma, Missao, MissaoAluno, Disciplina, Alternativa
        from accounts.models import Usuario

        # Dados básicos
        titulo = request.POST.get("titulo")
        descricao = request.POST.get("descricao", "")
        xp = request.POST.get("xp")
        disciplina_id = request.POST.get("disciplina")
        duracao = request.POST.get("duracao")
        turma_id = request.POST.get("turma")
        tipo = request.POST.get("tipo", "TAREFA")

        try:
            # Buscar turma e disciplina
            turma = Turma.objects.get(id=turma_id)
            disciplina = Disciplina.objects.get(id=disciplina_id) if disciplina_id else None

            # Criar a missão
            missao = Missao.objects.create(
                titulo=titulo,
                descricao=descricao if descricao else "Sem descrição",
                xp=xp,
                turma=turma,
                disciplina=disciplina,
                duracao=duracao if duracao else None,
                tipo=tipo,
                data_disponivel=timezone.now().date()
            )

            # Se for QUESTÃO, criar as alternativas
            if tipo == "QUESTAO":
                alternativa_a = request.POST.get("alternativa_a")
                alternativa_b = request.POST.get("alternativa_b")
                alternativa_c = request.POST.get("alternativa_c")
                alternativa_d = request.POST.get("alternativa_d")
                resposta_correta = request.POST.get("resposta_correta")

                # Criar as 4 alternativas
                alternativas_data = [
                    {'ordem': 'A', 'texto': alternativa_a},
                    {'ordem': 'B', 'texto': alternativa_b},
                    {'ordem': 'C', 'texto': alternativa_c},
                    {'ordem': 'D', 'texto': alternativa_d},
                ]

                for alt_data in alternativas_data:
                    Alternativa.objects.create(
                        missao=missao,
                        texto=alt_data['texto'],
                        ordem=alt_data['ordem'],
                        correta=(alt_data['ordem'] == resposta_correta)
                    )

                print(f"✅ QUESTÃO CRIADA: {missao.titulo} com 4 alternativas. Correta: {resposta_correta}")
            else:
                print(f"✅ TAREFA CRIADA: {missao.titulo}")

            # Atribuir a missão para todos os alunos da turma
            alunos = Usuario.objects.filter(tipo="ALUNO", turma=turma)
            for aluno in alunos:
                MissaoAluno.objects.create(
                    aluno=aluno,
                    missao=missao
                )

            print(f"✅ Missão atribuída para {alunos.count()} alunos")

        except Exception as e:
            print(f"❌ ERRO AO CRIAR MISSÃO: {e}")
            import traceback
            traceback.print_exc()

        return redirect("dashboard_professor")

    return redirect("dashboard_professor")


# =============================
# CONCLUIR MISSÃO - VERSÃO UNIFICADA COM NOTIFICAÇÕES
# =============================
@login_required
def concluir_missao(request, missao_aluno_id):
    from .models import MissaoAluno
    from accounts.models import Usuario
    from accounts.badges import verificar_e_conceder_badges

    missao_aluno = get_object_or_404(
        MissaoAluno,
        id=missao_aluno_id,
        aluno=request.user
    )

    if not missao_aluno.concluida:
        usuario = request.user
        
        # 🎯 Guardar estado ANTES das mudanças
        nivel_anterior = usuario.nivel
        streak_anterior = usuario.streak_atual
        
        # Marcar como concluída
        missao_aluno.concluida = True
        missao_aluno.data_conclusao = timezone.now().date()
        missao_aluno.save()

        # Adicionar XP e verificar se subiu de nível
        xp_ganho = missao_aluno.missao.xp
        subiu_nivel = usuario.adicionar_xp(xp_ganho)
        
        # Atualizar streak
        usuario.atualizar_streak_missao()
        
        # 🏆 VERIFICAR E CONCEDER BADGES
        badges_novas = verificar_e_conceder_badges(usuario)
        
        # 🎉 PREPARAR NOTIFICAÇÕES
        if badges_novas:
            request.session['badges_novas'] = [
                {'nome': badge.nome, 'icone': badge.icone} 
                for badge in badges_novas
            ]
        
        # ⭐ Notificar se subiu de nível
        if subiu_nivel:
            request.session['nivel_novo'] = usuario.nivel
        
        # 🔥 Notificar sobre streak
        if usuario.streak_atual > streak_anterior:
            # Streak aumentou
            tipo_streak = 'novo_recorde' if usuario.streak_atual > usuario.melhor_streak else 'manteve'
            request.session['streak_info'] = json.dumps({
                'dias': usuario.streak_atual,
                'tipo': tipo_streak
            })
        elif usuario.streak_atual == 0 and streak_anterior > 0:
            # Streak quebrou
            request.session['streak_info'] = json.dumps({
                'dias': streak_anterior,
                'tipo': 'perdeu'
            })

    return redirect("dashboard_aluno")


# =============================
# RESPONDER QUESTÃO - COM NOTIFICAÇÕES
# =============================
@login_required
def responder_questao(request, missao_aluno_id):
    from .models import MissaoAluno, Alternativa
    from accounts.badges import verificar_e_conceder_badges

    missao_aluno = get_object_or_404(
        MissaoAluno,
        id=missao_aluno_id,
        aluno=request.user
    )

    if request.method == "POST":
        usuario = request.user
        
        # 🎯 Guardar estado ANTES das mudanças
        nivel_anterior = usuario.nivel
        streak_anterior = usuario.streak_atual
        
        resposta = request.POST.get("resposta")  # A, B, C ou D
        
        # Buscar a alternativa correta
        alternativa_correta = Alternativa.objects.get(
            missao=missao_aluno.missao,
            correta=True
        )

        # Verificar se acertou
        acertou = (resposta == alternativa_correta.ordem)

        # Atualizar MissaoAluno
        missao_aluno.resposta_escolhida = resposta
        missao_aluno.acertou = acertou
        missao_aluno.concluida = True
        missao_aluno.data_conclusao = timezone.now().date()
        missao_aluno.save()

        # Dar XP e verificar badges APENAS se acertar
        if acertou:
            xp_ganho = missao_aluno.missao.xp
            subiu_nivel = usuario.adicionar_xp(xp_ganho)
            usuario.atualizar_streak_missao()
            
            # 🏆 VERIFICAR BADGES
            badges_novas = verificar_e_conceder_badges(usuario)
            
            # 🎉 PREPARAR NOTIFICAÇÕES
            if badges_novas:
                request.session['badges_novas'] = [
                    {'nome': badge.nome, 'icone': badge.icone} 
                    for badge in badges_novas
                ]
            
            # ⭐ Notificar se subiu de nível
            if subiu_nivel:
                request.session['nivel_novo'] = usuario.nivel
            
            # 🔥 Notificar sobre streak
            if usuario.streak_atual > streak_anterior:
                tipo_streak = 'novo_recorde' if usuario.streak_atual > usuario.melhor_streak else 'manteve'
                request.session['streak_info'] = json.dumps({
                    'dias': usuario.streak_atual,
                    'tipo': tipo_streak
                })

        return redirect("dashboard_aluno")

    # GET: Mostrar a questão
    alternativas = missao_aluno.missao.alternativas.all().order_by('ordem')
    
    context = {
        'missao_aluno': missao_aluno,
        'missao': missao_aluno.missao,
        'alternativas': alternativas,
    }
    
    return render(request, 'core/responder_questao.html', context)



@login_required
def historico_aluno(request):
    """Página de histórico de missões do aluno"""
    from .models import MissaoAluno, Disciplina
    
    # Buscar todas as missões do aluno (concluídas e pendentes)
    todas_missoes = MissaoAluno.objects.filter(
        aluno=request.user
    ).select_related('missao', 'missao__disciplina').order_by('-data_conclusao', '-missao__data_criacao')
    
    # Estatísticas gerais
    total_missoes = todas_missoes.count()
    concluidas = todas_missoes.filter(concluida=True).count()
    pendentes = total_missoes - concluidas
    
    # Questões respondidas
    questoes = todas_missoes.filter(missao__tipo='QUESTAO', concluida=True)
    total_questoes = questoes.count()
    acertos = questoes.filter(acertou=True).count()
    taxa_acerto = int((acertos / total_questoes * 100)) if total_questoes > 0 else 0
    
    # Disciplinas disponíveis para filtro
    disciplinas = Disciplina.objects.all()
    
    context = {
        'titulo': 'Histórico de Missões',
        'total_missoes': total_missoes,
        'concluidas': concluidas,
        'pendentes': pendentes,
        'total_questoes': total_questoes,
        'acertos': acertos,
        'taxa_acerto': taxa_acerto,
        'disciplinas': disciplinas,
    }
    
    return render(request, 'core/historico_aluno.html', context)


# =============================
# API: BUSCAR MISSÕES (AJAX)
# =============================
@login_required
def api_historico_aluno(request):
    """API para buscar missões do aluno com filtros"""
    from .models import MissaoAluno
    
    # Parâmetros de filtro
    filtro_status = request.GET.get('status', 'todas')  # todas, concluidas, pendentes
    filtro_disciplina = request.GET.get('disciplina', '')
    filtro_tipo = request.GET.get('tipo', '')  # QUESTAO, TAREFA
    busca = request.GET.get('busca', '')
    
    # Query base
    missoes = MissaoAluno.objects.filter(
        aluno=request.user
    ).select_related('missao', 'missao__disciplina', 'missao__turma')
    
    # Aplicar filtros
    if filtro_status == 'concluidas':
        missoes = missoes.filter(concluida=True)
    elif filtro_status == 'pendentes':
        missoes = missoes.filter(concluida=False)
    
    if filtro_disciplina:
        missoes = missoes.filter(missao__disciplina_id=filtro_disciplina)
    
    if filtro_tipo:
        missoes = missoes.filter(missao__tipo=filtro_tipo)
    
    if busca:
        missoes = missoes.filter(
            Q(missao__titulo__icontains=busca) |
            Q(missao__descricao__icontains=busca)
        )
    
    # Ordenar
    missoes = missoes.order_by('-data_conclusao', '-missao__data_criacao')
    
    # Limitar resultados (paginação simples)
    page = int(request.GET.get('page', 1))
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    
    missoes_page = missoes[start:end]
    has_more = missoes.count() > end
    
    # Serializar dados
    data = []
    for m in missoes_page:
        data.append({
            'id': m.id,
            'titulo': m.missao.titulo,
            'descricao': m.missao.descricao[:100],
            'xp': m.missao.xp,
            'disciplina': {
                'nome': m.missao.disciplina.nome if m.missao.disciplina else 'Sem disciplina',
                'icone': m.missao.disciplina.icone if m.missao.disciplina else '📚',
                'cor': m.missao.disciplina.cor if m.missao.disciplina else '#667eea',
            },
            'tipo': m.missao.tipo,
            'tipo_display': 'Questão' if m.missao.tipo == 'QUESTAO' else 'Tarefa',
            'turma': m.missao.turma.nome,
            'concluida': m.concluida,
            'data_criacao': m.missao.data_criacao.strftime('%d/%m/%Y'),
            'data_conclusao': m.data_conclusao.strftime('%d/%m/%Y') if m.data_conclusao else None,
            'acertou': m.acertou if m.missao.tipo == 'QUESTAO' else None,
            'resposta_escolhida': m.resposta_escolhida if m.missao.tipo == 'QUESTAO' else None,
        })
    
    return JsonResponse({
        'missoes': data,
        'has_more': has_more,
        'total': missoes.count(),
    })


# =============================
# HISTÓRICO DO PROFESSOR
# =============================
@login_required
def historico_professor(request):
    """Página de histórico de missões criadas pelo professor"""
    from .models import Missao, MissaoAluno, Disciplina
    
    # Buscar todas as missões criadas pelo professor
    turmas = request.user.turmas_professor.all()
    todas_missoes = Missao.objects.filter(
        turma__in=turmas
    ).select_related('disciplina', 'turma').order_by('-data_criacao')
    
    # Estatísticas
    total_missoes = todas_missoes.count()
    
    # Contar conclusões
    total_conclusoes = MissaoAluno.objects.filter(
        missao__in=todas_missoes,
        concluida=True
    ).count()
    
    # Contar atribuições totais
    total_atribuicoes = MissaoAluno.objects.filter(
        missao__in=todas_missoes
    ).count()
    
    taxa_conclusao = int((total_conclusoes / total_atribuicoes * 100)) if total_atribuicoes > 0 else 0
    
    # Disciplinas
    disciplinas = Disciplina.objects.all()
    
    context = {
        'titulo': 'Histórico de Missões Criadas',
        'total_missoes': total_missoes,
        'total_conclusoes': total_conclusoes,
        'total_atribuicoes': total_atribuicoes,
        'taxa_conclusao': taxa_conclusao,
        'turmas': turmas,
        'disciplinas': disciplinas,
    }
    
    return render(request, 'core/historico_professor.html', context)


# =============================
# API: MISSÕES DO PROFESSOR (AJAX)
# =============================
@login_required
def api_historico_professor(request):
    """API para buscar missões criadas pelo professor"""
    from .models import Missao, MissaoAluno
    
    # Filtros
    filtro_turma = request.GET.get('turma', '')
    filtro_disciplina = request.GET.get('disciplina', '')
    filtro_tipo = request.GET.get('tipo', '')
    busca = request.GET.get('busca', '')
    
    # Query base
    turmas = request.user.turmas_professor.all()
    missoes = Missao.objects.filter(turma__in=turmas).select_related(
        'disciplina', 'turma'
    )
    
    # Aplicar filtros
    if filtro_turma:
        missoes = missoes.filter(turma_id=filtro_turma)
    
    if filtro_disciplina:
        missoes = missoes.filter(disciplina_id=filtro_disciplina)
    
    if filtro_tipo:
        missoes = missoes.filter(tipo=filtro_tipo)
    
    if busca:
        missoes = missoes.filter(
            Q(titulo__icontains=busca) |
            Q(descricao__icontains=busca)
        )
    
    # Ordenar
    missoes = missoes.order_by('-data_criacao')
    
    # Paginação
    page = int(request.GET.get('page', 1))
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    
    missoes_page = missoes[start:end]
    has_more = missoes.count() > end
    
    # Serializar
    data = []
    for missao in missoes_page:
        # Contar conclusões
        atribuicoes = MissaoAluno.objects.filter(missao=missao)
        total_alunos = atribuicoes.count()
        concluidas = atribuicoes.filter(concluida=True).count()
        taxa = int((concluidas / total_alunos * 100)) if total_alunos > 0 else 0
        
        data.append({
            'id': missao.id,
            'titulo': missao.titulo,
            'descricao': missao.descricao[:100],
            'xp': missao.xp,
            'disciplina': {
                'nome': missao.disciplina.nome if missao.disciplina else 'Sem disciplina',
                'icone': missao.disciplina.icone if missao.disciplina else '📚',
                'cor': missao.disciplina.cor if missao.disciplina else '#667eea',
            },
            'tipo': missao.tipo,
            'tipo_display': 'Questão' if missao.tipo == 'QUESTAO' else 'Tarefa',
            'turma': missao.turma.nome,
            'data_criacao': missao.data_criacao.strftime('%d/%m/%Y às %H:%M'),
            'total_alunos': total_alunos,
            'concluidas': concluidas,
            'taxa_conclusao': taxa,
        })
    
    return JsonResponse({
        'missoes': data,
        'has_more': has_more,
        'total': missoes.count(),
    })


# =============================
# DETALHES DA MISSÃO (PROFESSOR)
# =============================
@login_required
def detalhes_missao(request, missao_id):
    """Ver quem completou uma missão específica"""
    from .models import Missao, MissaoAluno
    
    missao = get_object_or_404(Missao, id=missao_id)
    
    # Verificar se o professor é dono dessa missão
    if missao.turma.professor != request.user:
        return redirect('dashboard_professor')
    
    # Buscar todos os alunos que receberam essa missão
    alunos_missao = MissaoAluno.objects.filter(
        missao=missao
    ).select_related('aluno').order_by('-concluida', 'aluno__username')
    
    # Estatísticas
    total_alunos = alunos_missao.count()
    concluidas = alunos_missao.filter(concluida=True).count()
    pendentes = total_alunos - concluidas
    
    # Se for questão, calcular taxa de acerto
    acertos = None
    taxa_acerto = None
    if missao.tipo == 'QUESTAO':
        respondidas = alunos_missao.filter(concluida=True, missao__tipo='QUESTAO')
        total_respondidas = respondidas.count()
        acertos = respondidas.filter(acertou=True).count()
        taxa_acerto = int((acertos / total_respondidas * 100)) if total_respondidas > 0 else 0
    
    context = {
        'titulo': f'Detalhes: {missao.titulo}',
        'missao': missao,
        'alunos_missao': alunos_missao,
        'total_alunos': total_alunos,
        'concluidas': concluidas,
        'pendentes': pendentes,
        'acertos': acertos,
        'taxa_acerto': taxa_acerto,
    }
    
    return render(request, 'core/detalhes_missao.html', context)