"""Create missing learning_analytics tables if they do not exist.

This migration is defensive: it uses CREATE TABLE IF NOT EXISTS so that it
can be safely applied on databases where the initial migration was recorded
but the underlying tables are absent (for example due to manual truncation
or a failed earlier migration run).

It creates the CourseCreditHours and StudentCourseProgress tables used by
the learning_analytics app.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning_analytics', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS `learning_analytics_coursecredithours` (
                `id` bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `course_id` varchar(255) NOT NULL,
                `credit_hours` double NOT NULL,
                `course_name` varchar(255) NOT NULL,
                `created_by_id` bigint NULL,
                `created_at` datetime NOT NULL,
                `updated_at` datetime NOT NULL,
                UNIQUE (`course_id`),
                INDEX (`created_by_id`)
                -- Foreign key intentionally omitted for compatibility with differing auth_user id types
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

            CREATE TABLE IF NOT EXISTS `learning_analytics_studentcourseprogress` (
                `id` bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `user_id` bigint NOT NULL,
                `course_id` varchar(255) NOT NULL,
                `status` varchar(20) NOT NULL DEFAULT 'not_started',
                `enrollment_date` datetime NOT NULL,
                `completion_date` datetime NULL,
                `credit_hours_earned` double NOT NULL DEFAULT 0,
                `progress_percentage` double NOT NULL DEFAULT 0,
                `last_activity_date` datetime NULL,
                INDEX (`user_id`),
                UNIQUE (`user_id`,`course_id`)
                -- Foreign key intentionally omitted for compatibility with differing auth_user id types
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS `learning_analytics_studentcourseprogress`;
            DROP TABLE IF EXISTS `learning_analytics_coursecredithours`;
            """,
        ),
    ]
