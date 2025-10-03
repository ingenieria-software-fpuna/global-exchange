from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
    # URLs para Tausers
    path('', views.TauserListView.as_view(), name='tauser_list'),
    path('crear/', views.TauserCreateView.as_view(), name='tauser_create'),
    path('<int:pk>/', views.TauserDetailView.as_view(), name='tauser_detail'),
    path('<int:pk>/editar/', views.TauserUpdateView.as_view(), name='tauser_update'),
    path('<int:pk>/toggle-status/', views.toggle_tauser_status, name='tauser_toggle_status'),
    
    # URLs para Cargar Stock (solo desde tauser)
    path('<int:pk>/cargar-stock/', views.cargar_stock, name='cargar_stock'),
]
