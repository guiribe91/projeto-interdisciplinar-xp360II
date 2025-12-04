from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
@login_required
def criar_missao(request):
    if request.method == "POST":

        titulo = request.POST.get("titulo")
        descricao = request.POST.get("descricao", "")
        xp = request.POST.get("xp")
        disciplina = request.POST.get("disciplina")
        duracao = request.POST.get("duracao")
        turma_nome = request.POST.get("turma")

        from .models import Turma, Missao, MissaoAluno
        from accounts.models import Usuario

        try:
            turma = Turma.objects.get(nome=turma_nome)

            missao = Missao.objects.create(
                titulo=titulo,
                descricao=descricao if descricao else "Sem descrição",
                xp=xp,
                turma=turma,
                disciplina=disciplina,
                duracao=duracao
            )

            # ATRIBUIR MISSÃO AOS ALUNOS DA TURMA
            alunos = Usuario.objects.filter(tipo="ALUNO", turma=turma)

            for aluno in alunos:
                MissaoAluno.objects.create(
                    aluno=aluno,
                    missao=missao
                )

        except Exception as e:
            print("❌ ERRO AO CRIAR MISSÃO:", e)

        return redirect("dashboard_professor")

    return redirect("dashboard_professor")



@login_required
def concluir_missao(request, missao_aluno_id):  # ← Mudei o parâmetro
    """Função para o aluno concluir uma missão"""
    from .models import MissaoAluno
    from django.utils import timezone
    
    try:
        # Busca pelo ID do MissaoAluno, não da Missao
        missao_aluno = MissaoAluno.objects.get(
            id=missao_aluno_id,  # ← Mudei aqui
            aluno=request.user
        )
        
        if not missao_aluno.concluida:
            # Marca como concluída
            missao_aluno.concluida = True
            missao_aluno.data_conclusao = timezone.now().date()
            missao_aluno.save()
            
            # Atualiza XP do aluno
            xp_ganho = missao_aluno.missao.xp
            subiu_nivel = request.user.adicionar_xp(xp_ganho)
            
            print(f"✅ Missão '{missao_aluno.missao.titulo}' concluída por {request.user.username}")
            print(f"🎯 +{xp_ganho} XP! Total: {request.user.xp_total} XP | Nível: {request.user.nivel}")
            
            if subiu_nivel:
                print(f"🎊 LEVEL UP! {request.user.username} subiu para o nível {request.user.nivel}!")
        else:
            print(f"⚠️ Missão já estava concluída")
        
    except MissaoAluno.DoesNotExist:
        print(f"❌ MissaoAluno {missao_aluno_id} não encontrada ou não pertence ao usuário {request.user.username}")
    except Exception as e:
        print(f"❌ ERRO ao concluir missão: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect('dashboard_aluno')