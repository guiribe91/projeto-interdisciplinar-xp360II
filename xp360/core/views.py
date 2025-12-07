from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json


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