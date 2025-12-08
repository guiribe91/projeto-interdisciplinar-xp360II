# accounts/urls.py

from django.urls import path
from . import views


urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/aluno/', views.cadastro_aluno, name='cadastro_aluno'),
    path('cadastro/professor/', views.cadastro_professor, name='cadastro_professor'),
    
    # Dashboards
    path('dashboard/aluno/', views.dashboard_aluno, name='dashboard_aluno'),
    path('dashboard/professor/', views.dashboard_professor, name='dashboard_professor'),
    
    # Gerenciar Turmas
    path('criar-turma/', views.criar_turma, name='criar_turma'),
    path('editar-turma/<int:turma_id>/', views.editar_turma, name='editar_turma'),
    path('deletar-turma/<int:turma_id>/', views.deletar_turma, name='deletar_turma'),
    path('detalhes-turma/<int:turma_id>/', views.detalhes_turma, name='detalhes_turma'),
    
    # Ranking e Conquistas
    path('ranking/', views.ranking, name='ranking'),
    path('conquistas/', views.conquistas, name='conquistas'),

    # NOVAS URLs
    path('politica-privacidade/', views.PoliticaPrivacidadeView.as_view(), name='politica_privacidade'),
    path('termos-uso/', views.TermosUsoView.as_view(), name='termos_uso'),
]
