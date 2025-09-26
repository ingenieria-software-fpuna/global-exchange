from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import ConfiguracionSistema


class ConfiguracionSistemaModelTest(TestCase):
    """
    Pruebas para el modelo ConfiguracionSistema.
    """
    
    def test_crear_configuracion_por_defecto(self):
        """Test que se puede crear una configuración con valores por defecto."""
        config = ConfiguracionSistema.objects.create()
        self.assertEqual(config.limite_diario_transacciones, 0)
        self.assertEqual(config.limite_mensual_transacciones, 0)
    
    def test_get_configuracion_crea_instancia_si_no_existe(self):
        """Test que get_configuracion crea una instancia si no existe."""
        self.assertEqual(ConfiguracionSistema.objects.count(), 0)
        config = ConfiguracionSistema.get_configuracion()
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
        self.assertIsInstance(config, ConfiguracionSistema)
    
    def test_get_configuracion_retorna_existente(self):
        """Test que get_configuracion retorna la instancia existente."""
        config_original = ConfiguracionSistema.objects.create(
            limite_diario_transacciones=1000,
            limite_mensual_transacciones=30000
        )
        config_obtenida = ConfiguracionSistema.get_configuracion()
        self.assertEqual(config_obtenida.id, config_original.id)
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
    
    def test_save_actualiza_existente_si_no_tiene_pk(self):
        """Test que save actualiza la instancia existente si no tiene pk."""
        config_existente = ConfiguracionSistema.objects.create(
            limite_diario_transacciones=1000,
            limite_mensual_transacciones=30000
        )
        
        nueva_config = ConfiguracionSistema(
            limite_diario_transacciones=2000,
            limite_mensual_transacciones=60000
        )
        resultado = nueva_config.save()
        
        # Verificar que se actualizó la configuración existente
        config_existente.refresh_from_db()
        self.assertEqual(config_existente.limite_diario_transacciones, 2000)
        self.assertEqual(config_existente.limite_mensual_transacciones, 60000)
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
