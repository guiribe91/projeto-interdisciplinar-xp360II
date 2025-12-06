from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone


# =============================
# CRIAR MISSÃO
# =============================
@login_required
def criar_missao(request):
    if request.method == "POST":

        from .models import Turma, Missao, MissaoAluno
        from accounts.models import Usuario

        titulo = request.POST.get("titulo")
        descricao = request.POST.get("descricao", "")
        xp = request.POST.get("xp")
        disciplina = request.POST.get("disciplina")
        duracao = request.POST.get("duracao")
        turma_id = request.POST.get("turma")  # ← Renomeado para deixar claro que é ID

        try:
            # ✅ CORREÇÃO: Buscar por ID ao invés de nome
            turma = Turma.objects.get(id=turma_id)

            missao = Missao.objects.create(
                titulo=titulo,
                descricao=descricao if descricao else "Sem descrição",
                xp=xp,
                turma=turma,
                disciplina=disciplina,
                duracao=duracao,
                data_disponivel=timezone.now().date()
            )

            # Atribuir a missão para todos os alunos da turma
            alunos = Usuario.objects.filter(tipo="ALUNO", turma=turma)

            for aluno in alunos:
                MissaoAluno.objects.create(
                    aluno=aluno,
                    missao=missao
                )

            print(f"✅ MISSÃO CRIADA: {missao.titulo} para turma {turma.nome}")

        except Turma.DoesNotExist:
            print(f"❌ ERRO: Turma com ID {turma_id} não existe")
        except Exception as e:
            print(f"❌ ERRO AO CRIAR MISSÃO: {e}")

        return redirect("dashboard_professor")

    return redirect("dashboard_professor")


# =============================
# CONCLUIR MISSÃO
# =============================
@login_required
def concluir_missao(request, missao_aluno_id):

    from .models import MissaoAluno
    from accounts.models import Usuario

    missao_aluno = get_object_or_404(
        MissaoAluno,
        id=missao_aluno_id,
        aluno=request.user
    )

    if not missao_aluno.concluida:

        missao_aluno.concluida = True
        missao_aluno.data_conclusao = timezone.now().date()
        missao_aluno.save()

        # XP
        xp_ganho = missao_aluno.missao.xp
        usuario = request.user
        subiu_nivel = usuario.adicionar_xp(xp_ganho)
        
        # 🔥 NOVO: Atualizar streak
        usuario.atualizar_streak_missao()

    return redirect("dashboard_aluno")