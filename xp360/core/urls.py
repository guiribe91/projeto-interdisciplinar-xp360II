from django.urls import path
from . import views

urlpatterns = [
    # Missões
    path('criar-missao/', views.criar_missao, name='criar_missao'),
    path('concluir-missao/<int:missao_aluno_id>/', views.concluir_missao, name='concluir_missao'),
    path('responder/<int:missao_aluno_id>/', views.responder_questao, name='responder_questao'),
    
    # 🆕 HISTÓRICO - ALUNO
    path('historico/aluno/', views.historico_aluno, name='historico_aluno'),
    path('api/historico/aluno/', views.api_historico_aluno, name='api_historico_aluno'),
    
    # 🆕 HISTÓRICO - PROFESSOR
    path('historico/professor/', views.historico_professor, name='historico_professor'),
    path('api/historico/professor/', views.api_historico_professor, name='api_historico_professor'),
    path('missao/<int:missao_id>/detalhes/', views.detalhes_missao, name='detalhes_missao'),
]