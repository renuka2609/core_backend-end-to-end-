from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from orgs.models import Organization
from vendors.models import Vendor
from templates.models import Template, TemplateVersion, TemplateSection, TemplateQuestion
from assessments.models import Assessment
from responses.models import Response as ResponseModel
from permissions.constants import Roles
import uuid

class Command(BaseCommand):
    help = "Seed initial org, users, and admin"

    def handle(self, *args, **options):
        User = get_user_model()

        # Create Organization
        org, _ = Organization.objects.get_or_create(name="Demo Organization")
        self.stdout.write(self.style.SUCCESS("✅ Organization ready"))

        # Create Admin User
        admin_email = "admin@example.com"
        admin_username = "admin"
        if not User.objects.filter(email=admin_email).exists():
            # ensure required fields for custom User model are provided
            User.objects.create_superuser(username=admin_username, email=admin_email, password="admin123", org=org, role=Roles.ADMIN)
            self.stdout.write(self.style.SUCCESS("✅ Admin user created"))
        else:
            self.stdout.write("ℹ️ Admin user already exists")

        # Create Vendor and Vendor User
        vendor, _ = Vendor.objects.get_or_create(org=org, name="Demo Vendor")
        self.stdout.write(self.style.SUCCESS("✅ Vendor ready"))

        vendor_email = "vendor@example.com"
        vendor_username = "vendor"
        if not User.objects.filter(email=vendor_email).exists():
            User.objects.create_user(username=vendor_username, email=vendor_email, password="vendor123", org=org, role=Roles.VENDOR)
            self.stdout.write(self.style.SUCCESS("✅ Vendor user created"))
        else:
            self.stdout.write("ℹ️ Vendor user already exists")

        # Create Reviewer User
        reviewer_email = "reviewer@example.com"
        reviewer_username = "reviewer"
        if not User.objects.filter(email=reviewer_email).exists():
            User.objects.create_user(username=reviewer_username, email=reviewer_email, password="reviewer123", org=org, role=Roles.REVIEWER)
            self.stdout.write(self.style.SUCCESS("✅ Reviewer user created"))
        else:
            self.stdout.write("ℹ️ Reviewer user already exists")

        # Create a Template with a Version, Section and Question
        template, _ = Template.objects.get_or_create(name="Demo Template", description="Seeded template")
        tv, _ = TemplateVersion.objects.get_or_create(template=template, version=1, is_active=True)
        section, _ = TemplateSection.objects.get_or_create(template_version=tv, title="General", description="General questions")
        question, _ = TemplateQuestion.objects.get_or_create(section=section, text="What is your service?", question_type="text")
        self.stdout.write(self.style.SUCCESS("✅ Template + version + section + question created"))

        # Create a sample Assessment assigned to the Demo Vendor
        try:
            assessment = Assessment.objects.filter(org=org, vendor=vendor, template=template).first()
            if not assessment:
                assessment = Assessment.objects.create(org=org, vendor=vendor, template=template)
                self.stdout.write(self.style.SUCCESS("✅ Sample assessment created"))
            else:
                self.stdout.write("ℹ️ Sample assessment already exists")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Assessment creation issue: {e}"))

        # Create a sample Response for the assessment
        if assessment:
            try:
                r, _ = ResponseModel.objects.get_or_create(assessment=assessment, question_id=uuid.uuid4(), answer_text="Sample answer", submitted=False)
                self.stdout.write(self.style.SUCCESS("✅ Sample response created"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Response creation issue: {e}"))

        self.stdout.write(self.style.SUCCESS("🎉 Seeding completed"))
