from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.queues.models import Department, ServiceType
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds initial data for departments, service types, and an admin user'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial data...')

        # 1. Create Departments
        departments_data = [
            {'name': 'Registration', 'description': 'Main registration desk'},
            {'name': 'Payment', 'description': 'Cashier and payment services'},
            {'name': 'Inquiry', 'description': 'General information and inquiries'},
        ]

        departments = {}
        for dept_info in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_info['name'],
                defaults={
                    'description': dept_info['description'],
                    'slug': slugify(dept_info['name'])
                }
            )
            departments[dept.name] = dept
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {dept.name}'))
            else:
                self.stdout.write(f'Department already exists: {dept.name}')

        # 2. Create Service Types
        services_data = [
            {'name': 'New Student Registration', 'prefix': 'REG', 'department': 'Registration'},
            {'name': 'Tuition Fee Payment', 'prefix': 'PAY', 'department': 'Payment'},
            {'name': 'General Inquiry', 'prefix': 'INQ', 'department': 'Inquiry'},
        ]

        for svc_info in services_data:
            dept = departments.get(svc_info['department'])
            svc, created = ServiceType.objects.get_or_create(
                name=svc_info['name'],
                defaults={
                    'prefix': svc_info['prefix'],
                    'department': dept,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created service type: {svc.name}'))
            else:
                self.stdout.write(f'Service type already exists: {svc.name}')

        # 3. Create initial Admin User if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            from apps.accounts.models import CustomRole
            admin_role = CustomRole.objects.get(slug='admin')
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            admin_user.custom_role = admin_role
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created superuser: admin'))
        else:
            self.stdout.write('Superuser "admin" already exists')

        self.stdout.write(self.style.SUCCESS('Data seeding complete.'))
