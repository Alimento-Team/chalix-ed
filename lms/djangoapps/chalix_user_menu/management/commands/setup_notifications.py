"""
Management command to setup initial notification types and create sample notifications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from lms.djangoapps.chalix_user_menu.models import NotificationType, Notification


class Command(BaseCommand):
    help = 'Setup initial notification types and create sample notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-samples',
            action='store_true',
            help='Create sample notifications for all users',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up notification system...'))

        # Create notification types
        notification_types = [
            {
                'name': 'course_enrollment',
                'display_name': _('Đăng ký khóa học'),
                'description': _('Thông báo về việc đăng ký khóa học thành công')
            },
            {
                'name': 'course_completion',
                'display_name': _('Hoàn thành khóa học'),
                'description': _('Thông báo khi hoàn thành khóa học')
            },
            {
                'name': 'assignment_due',
                'display_name': _('Hạn nộp bài tập'),
                'description': _('Nhắc nhở về hạn nộp bài tập')
            },
            {
                'name': 'grade_updated',
                'display_name': _('Cập nhật điểm số'),
                'description': _('Thông báo khi điểm số được cập nhật')
            },
            {
                'name': 'teaching_request_status',
                'display_name': _('Trạng thái đăng ký giảng dạy'),
                'description': _('Thông báo về trạng thái đơn đăng ký giảng dạy')
            },
            {
                'name': 'system_announcement',
                'display_name': _('Thông báo hệ thống'),
                'description': _('Thông báo quan trọng từ hệ thống')
            },
            {
                'name': 'certificate_ready',
                'display_name': _('Chứng chỉ sẵn sàng'),
                'description': _('Thông báo khi chứng chỉ đã sẵn sàng để tải')
            },
            {
                'name': 'discussion_reply',
                'display_name': _('Phản hồi thảo luận'),
                'description': _('Thông báo khi có phản hồi trong diễn đàn thảo luận')
            }
        ]

        created_count = 0
        for type_data in notification_types:
            notification_type, created = NotificationType.objects.get_or_create(
                name=type_data['name'],
                defaults={
                    'display_name': type_data['display_name'],
                    'description': type_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created notification type: {type_data['display_name']}")

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} notification types')
        )

        # Create sample notifications if requested
        if options['create_samples']:
            self.create_sample_notifications()

    def create_sample_notifications(self):
        """Create sample notifications for demonstration"""
        self.stdout.write('Creating sample notifications...')

        # Get all users (limit to first 10 for demo)
        users = User.objects.all()[:10]
        if not users:
            self.stdout.write(self.style.WARNING('No users found. Skipping sample notifications.'))
            return

        # Get notification types
        course_enrollment_type = NotificationType.objects.get(name='course_enrollment')
        system_announcement_type = NotificationType.objects.get(name='system_announcement')
        teaching_request_type = NotificationType.objects.get(name='teaching_request_status')

        sample_notifications = [
            {
                'title': 'Bạn đăng ký khóa học Lập trình Nodejs thành công!',
                'message': 'Chúc mừng bạn đã đăng ký thành công khóa học "Lập trình Nodejs từ zero tới master". Hãy bắt đầu học ngay hôm nay!',
                'notification_type': course_enrollment_type,
                'priority': 'medium',
                'action_url': '/courses',
                'action_text': 'Xem khóa học'
            },
            {
                'title': 'Hệ thống bảo trì định kỳ',
                'message': 'Hệ thống sẽ được bảo trì vào 2:00 AM ngày mai. Vui lòng hoàn thành các bài học trước thời gian này.',
                'notification_type': system_announcement_type,
                'priority': 'high',
                'action_url': '/announcements',
                'action_text': 'Xem chi tiết'
            },
            {
                'title': 'Đơn đăng ký giảng dạy được phê duyệt',
                'message': 'Đơn đăng ký giảng dạy khóa học "Python cơ bản" của bạn đã được phê duyệt. Chúc mừng bạn!',
                'notification_type': teaching_request_type,
                'priority': 'high',
                'action_url': '/teaching/dashboard',
                'action_text': 'Xem chi tiết'
            }
        ]

        notifications_created = 0
        for user in users:
            for i, notification_data in enumerate(sample_notifications):
                # Create notifications with different timestamps
                import datetime
                from django.utils import timezone

                created_at = timezone.now() - datetime.timedelta(
                    minutes=i * 30 + (user.id * 2)  # Stagger creation times
                )

                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_data['notification_type'],
                    title=notification_data['title'],
                    message=notification_data['message'],
                    priority=notification_data['priority'],
                    action_url=notification_data['action_url'],
                    action_text=notification_data['action_text'],
                    is_read=(i > 0),  # Mark first notification as unread
                )
                # Set custom created_at
                notification.created_at = created_at
                notification.save(update_fields=['created_at'])

                notifications_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {notifications_created} sample notifications')
        )
