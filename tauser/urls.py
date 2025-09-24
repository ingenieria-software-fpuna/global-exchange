from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
    path('', views.TauserListView.as_view(), name='tauser_list'),
    path('crear/', views.TauserCreateView.as_view(), name='tauser_create'),
    path('<int:pk>/editar/', views.TauserUpdateView.as_view(), name='tauser_update'),
    path('<int:pk>/toggle-status/', views.toggle_tauser_status, name='tauser_toggle_status'),
]
