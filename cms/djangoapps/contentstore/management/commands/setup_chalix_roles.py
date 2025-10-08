"""
Management command to setup initial Chalix role system data
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixUserRole
from common.djangoapps.student.roles import GlobalStaff


class Command(BaseCommand):
    """
    Setup initial Chalix role system data including organizations and roles.
    
    Example usage:
        python manage.py cms setup_chalix_roles
        python manage.py cms setup_chalix_roles --create-sample-users
    """
    
    help = 'Setup initial Chalix role system data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-users',
            action='store_true',
            dest='create_sample_users',
            default=False,
            help='Create sample users for each role type'
        )
        
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help='Reset existing data (WARNING: This will delete existing roles and organizations)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(
                self.style.WARNING('Resetting existing Chalix role data...')
            )
            ChalixUserRole.objects.all().delete()
            ChalixOrganization.objects.all().delete()
            
        self._create_organizations()
        
        if options['create_sample_users']:
            self._create_sample_users()
            
        self.stdout.write(
            self.style.SUCCESS('Successfully setup Chalix role system')
        )

    def _create_organizations(self):
        """Create initial organizations"""
        self.stdout.write('Creating organizations...')
        
        # Main department organization (single account)
        dept_org, created = ChalixOrganization.objects.get_or_create(
            name='main_department',
            defaults={
                'display_name': 'Main Department',
                'code': 'DEPT001',
                'description': 'Main department organization with single account',
                'is_active': True,
                'parent': None
            }
        )
        if created:
            self.stdout.write(f'Created organization: {dept_org.display_name}')
        
        # Sample divisions (multiple accounts)
        divisions = [
            {
                'name': 'engineering_division',
                'display_name': 'Engineering Division',
                'code': 'ENG001',
                'description': 'Engineering division for technical courses'
            },
            {
                'name': 'business_division',
                'display_name': 'Business Division', 
                'code': 'BUS001',
                'description': 'Business division for management courses'
            },
            {
                'name': 'education_division',
                'display_name': 'Education Division',
                'code': 'EDU001', 
                'description': 'Education division for training programs'
            }
        ]
        
        for div_data in divisions:
            div_org, created = ChalixOrganization.objects.get_or_create(
                name=div_data['name'],
                defaults={
                    'display_name': div_data['display_name'],
                    'code': div_data['code'],
                    'description': div_data['description'],
                    'is_active': True,
                    'parent': dept_org
                }
            )
            if created:
                self.stdout.write(f'Created division: {div_org.display_name}')

    def _create_sample_users(self):
        """Create sample users for each role type"""
        self.stdout.write('Creating sample users...')
        
        try:
            dept_org = ChalixOrganization.objects.get(name='main_department')
            eng_div = ChalixOrganization.objects.get(name='engineering_division')
        except ChalixOrganization.DoesNotExist:
            raise CommandError('Organizations not found. Run without --create-sample-users first.')
        
        # Create department user (only one allowed - 'bo' role)
        dept_user = self._create_user(
            username='bo_admin',
            email='bo.admin@chalix.edu',
            first_name='Bộ',
            last_name='Administrator'
        )
        ChalixUserRole.objects.get_or_create(
            user=dept_user,
            role='bo',  # Department level - single account
            organization=dept_org,
            defaults={'is_active': True}
        )
        
        # Create organization users (multiple allowed - 'co_quan' role)
        for i in range(1, 3):
            org_user = self._create_user(
                username=f'co_quan_manager_{i}',
                email=f'co.quan.manager{i}@chalix.edu',
                first_name='Cơ quan',
                last_name=f'Manager {i}'
            )
            ChalixUserRole.objects.get_or_create(
                user=org_user,
                role='co_quan',  # Organization level - multiple accounts
                organization=eng_div,
                defaults={'is_active': True}
            )
        
        # Create instructor users (multiple allowed - 'giang_vien' role)
        for i in range(1, 4):
            instructor = self._create_user(
                username=f'giang_vien_{i}',
                email=f'giang.vien{i}@chalix.edu',
                first_name='Giảng viên',
                last_name=f'{i}'
            )
            ChalixUserRole.objects.get_or_create(
                user=instructor,
                role='giang_vien',  # Teacher/Instructor level - multiple accounts
                organization=eng_div,
                defaults={'is_active': True}
            )
        
        # Create learner users (multiple allowed - 'cong_chuc' role)
        for i in range(1, 6):
            learner = self._create_user(
                username=f'cong_chuc_{i}',
                email=f'cong.chuc{i}@chalix.edu',
                first_name='Công chức',
                last_name=f'{i}'
            )
            ChalixUserRole.objects.get_or_create(
                user=learner,
                role='cong_chuc',  # Learner/Student level - multiple accounts
                organization=eng_div,
                defaults={'is_active': True}
            )

    def _create_user(self, username, email, first_name, last_name):
        """Create or get user"""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            }
        )
        if created:
            user.set_password('password123')  # Set default password
            user.save()
            self.stdout.write(f'Created user: {username} ({email})')
        return user