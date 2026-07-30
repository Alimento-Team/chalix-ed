"""
Backfill Chalix user roles for users imported before role-assignment fixes.

This command is intentionally conservative by default:
- Only considers active users with no active Chalix role.
- Only assigns users whose profile.meta['don_vi_cong_tac'] matches the target organization.
- Supports --dry-run for safe preview.
"""

import unicodedata

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from common.djangoapps.student.models import UserProfile

from cms.djangoapps.contentstore.models import ChalixOrganization, ChalixUserRole


def normalize_text(value):
    """Normalize text for robust matching: lowercase, strip accents, compact spaces."""
    if value is None:
        return ''

    text = str(value).strip().lower()
    if not text:
        return ''

    text = text.replace('-', ' ').replace('_', ' ').replace('/', ' ')
    text = ' '.join(text.split())

    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


class Command(BaseCommand):
    help = (
        "Backfill role 'cong_chuc' for imported users that currently have no active Chalix role, "
        "scoped to a specific organization by matching profile.meta['don_vi_cong_tac']."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization-id',
            type=int,
            required=True,
            help='Target ChalixOrganization ID (example: 19).',
        )
        parser.add_argument(
            '--created-by',
            type=str,
            default='',
            help='Username used in ChalixUserRole.created_by (default: first superuser).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview only, do not write database changes.',
        )
        parser.add_argument(
            '--include-empty-org-meta',
            action='store_true',
            help=(
                'Also include users with empty don_vi_cong_tac in profile meta. '
                'Use with caution.'
            ),
        )

    def handle(self, *args, **options):
        org_id = options['organization_id']
        dry_run = options['dry_run']
        include_empty_org_meta = options['include_empty_org_meta']

        try:
            organization = ChalixOrganization.objects.get(id=org_id)
        except ChalixOrganization.DoesNotExist as exc:
            raise CommandError(f'Organization id={org_id} not found.') from exc

        User = get_user_model()
        created_by_username = (options.get('created_by') or '').strip()

        created_by = None
        if created_by_username:
            created_by = User.objects.filter(username=created_by_username).first()
            if not created_by:
                raise CommandError(f"User '{created_by_username}' not found for --created-by.")
        else:
            created_by = User.objects.filter(is_superuser=True).order_by('id').first()
            if not created_by:
                raise CommandError('No superuser found. Please pass --created-by <username>.')

        org_candidates = {
            normalize_text(organization.name),
            normalize_text(organization.display_name),
        }

        users_without_active_role = (
            User.objects
            .filter(is_active=True)
            .exclude(chalix_roles__is_active=True)
            .distinct()
            .order_by('id')
        )

        matched_users = []
        skipped_count = 0

        for user in users_without_active_role:
            profile = UserProfile.objects.filter(user=user).first()
            if not profile:
                skipped_count += 1
                continue

            try:
                meta = profile.get_meta() if hasattr(profile, 'get_meta') else {}
            except Exception:
                meta = {}

            org_meta_raw = (meta or {}).get('don_vi_cong_tac', '')
            org_meta_norm = normalize_text(org_meta_raw)

            if org_meta_norm:
                if org_meta_norm in org_candidates:
                    matched_users.append((user, org_meta_raw))
                else:
                    skipped_count += 1
            else:
                if include_empty_org_meta:
                    matched_users.append((user, org_meta_raw))
                else:
                    skipped_count += 1

        self.stdout.write(self.style.WARNING(
            f'[Preview] Org: {organization.display_name} (id={organization.id})'
        ))
        self.stdout.write(self.style.WARNING(
            f'[Preview] Users without active role: {users_without_active_role.count()}'
        ))
        self.stdout.write(self.style.WARNING(
            f'[Preview] Matched for backfill: {len(matched_users)} | Skipped: {skipped_count}'
        ))

        if not matched_users:
            self.stdout.write(self.style.SUCCESS('No users to backfill.'))
            return

        preview_limit = 20
        for user, org_meta_raw in matched_users[:preview_limit]:
            self.stdout.write(
                f" - {user.id} | {user.username} | {user.email} | don_vi_cong_tac='{org_meta_raw}'"
            )
        if len(matched_users) > preview_limit:
            self.stdout.write(f' ... and {len(matched_users) - preview_limit} more')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry-run finished. No database changes applied.'))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for user, _ in matched_users:
                existing = ChalixUserRole.objects.filter(
                    user=user,
                    role='cong_chuc',
                    organization=organization,
                ).first()

                if existing:
                    changed = False
                    if not existing.is_active:
                        existing.is_active = True
                        changed = True
                    if not existing.created_by_id and created_by:
                        existing.created_by = created_by
                        changed = True
                    if changed:
                        existing.save()
                        updated_count += 1
                else:
                    ChalixUserRole.objects.create(
                        user=user,
                        role='cong_chuc',
                        organization=organization,
                        is_active=True,
                        created_by=created_by,
                    )
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Backfill done. created={created_count}, updated={updated_count}, total={created_count + updated_count}'
        ))
