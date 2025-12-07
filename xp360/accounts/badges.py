"""
Sistema de Badges Automáticas
Verifica e concede badges quando o usuário atinge determinados marcos
"""

from .models import Badge, BadgeUsuario
from core.models import MissaoAluno


def verificar_e_conceder_badges(usuario):
    """
    Verifica todas as condições de badges e concede as que o usuário merece
    Retorna lista de badges recém conquistadas (para notificações)
    """
    badges_novas = []
    
    # 1. BADGES DE MISSÕES
    total_missoes = MissaoAluno.objects.filter(aluno=usuario, concluida=True).count()
    badges_missoes = Badge.objects.filter(tipo='MISSOES', condicao_valor__lte=total_missoes)
    
    for badge in badges_missoes:
        badge_conquistada, created = BadgeUsuario.objects.get_or_create(
            usuario=usuario,
            badge=badge
        )
        if created:
            badges_novas.append(badge)
    
    # 2. BADGES DE STREAK
    streak_atual = usuario.streak_atual
    badges_streak = Badge.objects.filter(tipo='STREAK', condicao_valor__lte=streak_atual)
    
    for badge in badges_streak:
        badge_conquistada, created = BadgeUsuario.objects.get_or_create(
            usuario=usuario,
            badge=badge
        )
        if created:
            badges_novas.append(badge)
    
    # 3. BADGES DE NÍVEL
    nivel_atual = usuario.nivel
    badges_nivel = Badge.objects.filter(tipo='NIVEL', condicao_valor__lte=nivel_atual)
    
    for badge in badges_nivel:
        badge_conquistada, created = BadgeUsuario.objects.get_or_create(
            usuario=usuario,
            badge=badge
        )
        if created:
            badges_novas.append(badge)
    
    # 4. BADGES DE PRECISÃO (Questões corretas seguidas)
    acertos_seguidos = calcular_acertos_seguidos(usuario)
    badges_precisao = Badge.objects.filter(tipo='PRECISAO', condicao_valor__lte=acertos_seguidos)
    
    for badge in badges_precisao:
        badge_conquistada, created = BadgeUsuario.objects.get_or_create(
            usuario=usuario,
            badge=badge
        )
        if created:
            badges_novas.append(badge)
    
    return badges_novas


def calcular_acertos_seguidos(usuario):
    """
    Calcula quantas questões o usuário acertou seguidas
    """
    missoes_questao = MissaoAluno.objects.filter(
        aluno=usuario,
        missao__tipo='QUESTAO',
        concluida=True
    ).order_by('-data_conclusao')[:20]  # Últimas 20 questões
    
    acertos_seguidos = 0
    
    for missao in missoes_questao:
        if missao.acertou:
            acertos_seguidos += 1
        else:
            break  # Para na primeira errada
    
    return acertos_seguidos


def get_progresso_badges(usuario):
    """
    Retorna informações sobre progresso em badges não conquistadas
    Útil para mostrar "falta X para desbloquear"
    """
    badges_conquistadas_ids = BadgeUsuario.objects.filter(
        usuario=usuario
    ).values_list('badge_id', flat=True)
    
    badges_pendentes = Badge.objects.exclude(id__in=badges_conquistadas_ids)
    
    progresso = []
    
    for badge in badges_pendentes:
        info = {
            'badge': badge,
            'atual': 0,
            'necessario': badge.condicao_valor,
            'porcentagem': 0
        }
        
        if badge.tipo == 'MISSOES':
            info['atual'] = MissaoAluno.objects.filter(aluno=usuario, concluida=True).count()
        elif badge.tipo == 'STREAK':
            info['atual'] = usuario.streak_atual
        elif badge.tipo == 'NIVEL':
            info['atual'] = usuario.nivel
        elif badge.tipo == 'PRECISAO':
            info['atual'] = calcular_acertos_seguidos(usuario)
        
        if info['necessario'] > 0:
            info['porcentagem'] = min(100, int((info['atual'] / info['necessario']) * 100))
        
        progresso.append(info)
    
    return progresso