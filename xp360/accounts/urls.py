from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cadastro/aluno/", views.cadastro_aluno, name="cadastro_aluno"),
    path("cadastro/professor/", views.cadastro_professor, name="cadastro_professor"),

    # Dashboards
    path("dashboard/aluno/", views.dashboard_aluno, name="dashboard_aluno"),
    path("dashboard/professor/", views.dashboard_professor, name="dashboard_professor"),

    path('turma/<int:turma_id>/', views.detalhes_turma, name='detalhes_turma'),

    path('ranking/', views.ranking, name='ranking'),
    path('conquistas/', views.conquistas, name='conquistas'),
   

]
