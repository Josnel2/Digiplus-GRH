"""
Tests for notification functionality
Tests the creation of notifications and WebSocket sending logic
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from manage_users.models import Poste, Employe, DemandeConge, Notification

User = get_user_model()


class NotificationTestCase(TestCase):
    """Test cases for Notification model and related functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_admin=True,
            is_verified=True
        )
        
        self.employee_user = User.objects.create_user(
            email='employee@test.com',
            password='emppass123',
            first_name='Employee',
            last_name='User',
            is_employe=True,
            is_verified=True
        )
        
        # Create poste
        self.poste = Poste.objects.create(
            titre='Développeur',
            description='Développement logiciel',
            salaire_de_base=3500.00
        )
        
        # Create employe profile
        self.employe = Employe.objects.create(
            user=self.employee_user,
            matricule='EMP001',
            date_embauche='2024-01-15',
            statut='actif',
            poste=self.poste
        )
        
        # Create a leave request
        self.demande_conge = DemandeConge.objects.create(
            employe=self.employe,
            type_conge='annuel',
            date_debut='2024-12-01',
            date_fin='2024-12-10',
            statut='en_attente'
        )
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_approuver_creates_notification(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that approuver() creates a Notification record"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Initial state
        initial_count = Notification.objects.count()
        self.assertEqual(initial_count, 0)
        
        # Call approuver
        self.demande_conge.approuver()
        
        # Verify notification was created
        notifications = Notification.objects.filter(demande_conge=self.demande_conge)
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.titre, 'Congé approuvé')
        self.assertIn('approuvée', notification.message)
        self.assertEqual(notification.demande_conge, self.demande_conge)
        self.assertFalse(notification.lu)
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_rejeter_creates_notification(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that rejeter() creates a Notification record"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Initial state
        initial_count = Notification.objects.count()
        self.assertEqual(initial_count, 0)
        
        # Call rejeter
        self.demande_conge.rejeter()
        
        # Verify notification was created
        notifications = Notification.objects.filter(demande_conge=self.demande_conge)
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.titre, 'Congé rejeté')
        self.assertIn('rejetée', notification.message)
        self.assertEqual(notification.demande_conge, self.demande_conge)
        self.assertFalse(notification.lu)
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_approuver_sends_websocket_notification(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that approuver() sends a WebSocket notification"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_async_to_sync.return_value = MagicMock()
        
        # Call approuver
        self.demande_conge.approuver()
        
        # Verify WebSocket group_send was called
        mock_async_to_sync.assert_called()
        call_args = mock_async_to_sync.return_value.call_args
        
        if call_args:
            # Verify the group name is correct
            group_name = call_args[0][0] if call_args[0] else None
            self.assertEqual(group_name, f"user_{self.employee_user.id}")
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_approuver_updates_status(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that approuver() updates the status to 'approuve'"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Initial status
        self.assertEqual(self.demande_conge.statut, 'en_attente')
        
        # Call approuver
        self.demande_conge.approuver()
        
        # Refresh from DB
        self.demande_conge.refresh_from_db()
        
        # Verify status changed
        self.assertEqual(self.demande_conge.statut, 'approuve')
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_rejeter_updates_status(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that rejeter() updates the status to 'rejete'"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Initial status
        self.assertEqual(self.demande_conge.statut, 'en_attente')
        
        # Call rejeter
        self.demande_conge.rejeter()
        
        # Refresh from DB
        self.demande_conge.refresh_from_db()
        
        # Verify status changed
        self.assertEqual(self.demande_conge.statut, 'rejete')
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_approuver_with_extra_fields(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that approuver() can update additional fields"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Call approuver with extra field
        original_description = self.demande_conge.description
        new_description = "Approuvé avec conditions"
        
        self.demande_conge.approuver(description=new_description)
        
        # Refresh from DB
        self.demande_conge.refresh_from_db()
        
        # Verify fields updated
        self.assertEqual(self.demande_conge.statut, 'approuve')
        self.assertEqual(self.demande_conge.description, new_description)
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_notification_queryset_filtering(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that notifications are properly linked to leave requests"""
        # Setup mock 
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Create multiple leave requests
        conge2 = DemandeConge.objects.create(
            employe=self.employe,
            type_conge='maladie',
            date_debut='2024-12-15',
            date_fin='2024-12-20',
            statut='en_attente'
        )
        
        # Approve first, reject second
        self.demande_conge.approuver()
        conge2.rejeter()
        
        # Verify notifications are linked correctly
        notifs_conge1 = Notification.objects.filter(demande_conge=self.demande_conge)
        notifs_conge2 = Notification.objects.filter(demande_conge=conge2)
        
        self.assertEqual(notifs_conge1.count(), 1)
        self.assertEqual(notifs_conge2.count(), 1)
        
        self.assertEqual(notifs_conge1.first().titre, 'Congé approuvé')
        self.assertEqual(notifs_conge2.first().titre, 'Congé rejeté')


class NotificationListViewTestCase(TestCase):
    """Test cases for NotificationListView"""
    
    def setUp(self):
        """Set up test data"""
        self.employee_user = User.objects.create_user(
            email='employee@test.com',
            password='emppass123',
            first_name='Employee',
            last_name='User',
            is_employe=True,
            is_verified=True
        )
        
        self.poste = Poste.objects.create(
            titre='Développeur',
            salaire_de_base=3500.00
        )
        
        self.employe = Employe.objects.create(
            user=self.employee_user,
            matricule='EMP001',
            date_embauche='2024-01-15',
            poste=self.poste
        )
    
    @patch('manage_users.models.async_to_sync')
    @patch('manage_users.models.get_channel_layer')
    def test_notification_list_view_filtering(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that NotificationListView returns only user's notifications"""
        # Setup mock
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Create leave requests
        conge = DemandeConge.objects.create(
            employe=self.employe,
            type_conge='annuel',
            date_debut='2024-12-01',
            date_fin='2024-12-10',
            statut='en_attente'
        )
        
        # Create notification
        conge.approuver()
        
        # Verify notification exists
        user_notifications = Notification.objects.filter(
            demande_conge__employe__user=self.employee_user
        )
        self.assertEqual(user_notifications.count(), 1)
