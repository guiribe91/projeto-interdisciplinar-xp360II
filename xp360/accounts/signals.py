"""
Signals para criar automaticamente MissaoAluno quando:
1. Um novo aluno é cadastrado
2. Uma nova missão é criada para uma turma
"""

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from accounts.models import Usuario
from core.models import Missao, MissaoAluno


@receiver(m2m_changed, sender=Usuario.turmas_aluno.through)
def criar_missoes_para_novo_aluno(sender, instance, action, pk_set, **kwargs):
    """
    Quando um aluno é associado a turmas, cria MissaoAluno
    para todas as missões existentes nessas turmas.
    """
    if action == "post_add" and instance.tipo == 'ALUNO':
        # pk_set contém os IDs das turmas que foram adicionadas
        from core.models import Turma
        
        for turma_id in pk_set:
            # Buscar todas as missões dessa turma
            missoes = Missao.objects.filter(turma_id=turma_id)
            
            # Criar MissaoAluno para cada missão
            for missao in missoes:
                MissaoAluno.objects.get_or_create(
                    aluno=instance,
                    missao=missao,
                    defaults={'concluida': False}
                )
            
            print(f"✅ Criadas {missoes.count()} missões para {instance.username} na turma {turma_id}")


@receiver(post_save, sender=Missao)
def criar_missao_aluno_para_todos_alunos(sender, instance, created, **kwargs):
    """
    Quando uma nova missão é criada, cria MissaoAluno
    para todos os alunos da turma.
    """
    if created:
        turma = instance.turma
        alunos = turma.alunos.all()
        
        # Criar MissaoAluno para cada aluno
        missoes_criadas = []
        for aluno in alunos:
            missao_aluno, criada = MissaoAluno.objects.get_or_create(
                aluno=aluno,
                missao=instance,
                defaults={'concluida': False}
            )
            if criada:
                missoes_criadas.append(missao_aluno)
        
        print(f"✅ Missão '{instance.titulo}' atribuída a {len(missoes_criadas)} alunos")