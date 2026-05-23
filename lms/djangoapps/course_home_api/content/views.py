"""
LMS Content API Views - Read-only mirrors of CMS contentstore APIs.
"""

import logging
from django.http import Http404
from django.shortcuts import get_object_or_404
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import requests
import urllib.parse
import os
from typing import Optional
import boto3  # type: ignore

from django.utils import timezone
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.core.exceptions import ObjectDoesNotExist
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum  # for branch selection
from xmodule.modulestore.exceptions import ItemNotFoundError
from django.apps import apps as django_apps
from lms.djangoapps.course_home_api.models import TopicQuizAttempt

# Re-use CMS models for unit media files and Chalix quizzes; DB is shared across LMS/CMS
# But avoid importing CMS models into the LMS process unless the CMS app is installed
CMSUnitMediaFile = None
CMSChalixQuiz = None
CMSChalixQuizQuestion = None
CMSChalixQuizChoice = None
try:
    # Try to import from CMS first if available
    if django_apps.is_installed('cms') or django_apps.is_installed('cms.djangoapps.contentstore'):
        from cms.djangoapps.contentstore.models import (
            UnitMediaFile as CMSUnitMediaFile,
            ChalixQuiz as CMSChalixQuiz,
            ChalixQuizQuestion as CMSChalixQuizQuestion,
            ChalixQuizChoice as CMSChalixQuizChoice,
        )
    else:
        # Fallback to unmanaged LMS mappings
        from lms.djangoapps.course_home_api.models import (
            UnitMediaFileLMS as CMSUnitMediaFile,
            ChalixQuizLMS as CMSChalixQuiz,
            ChalixQuizQuestionLMS as CMSChalixQuizQuestion,
            ChalixQuizChoiceLMS as CMSChalixQuizChoice,
        )
except Exception:
    # If imports fail for any reason, proceed without DB-backed media
    CMSUnitMediaFile = None
    CMSChalixQuiz = None
    CMSChalixQuizQuestion = None
    CMSChalixQuizChoice = None

LOGGER = logging.getLogger(__name__)


def extract_youtube_id(url):
    """
    Extract YouTube video ID from various YouTube URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    if not url:
        return None
        
    import re
    from urllib.parse import urlparse, parse_qs
    
    try:
        parsed = urlparse(url)
        
        # youtu.be format
        if 'youtu.be' in parsed.netloc:
            return parsed.path.lstrip('/')
        
        # youtube.com formats
        if 'youtube.com' in parsed.netloc:
            # Watch URL: ?v=VIDEO_ID
            if parsed.path == '/watch':
                qs = parse_qs(parsed.query)
                return qs.get('v', [None])[0]
            
            # Embed URL: /embed/VIDEO_ID
            if parsed.path.startswith('/embed/'):
                return parsed.path.replace('/embed/', '')
        
        # Fallback: regex search for 11-character YouTube ID pattern
        match = re.search(r'[a-zA-Z0-9_-]{11}', url)
        return match.group(0) if match else None
        
    except Exception:
        return None


class CMSProxyMixin:
    """
    Mixin to provide CMS proxy functionality for content APIs.
    """
    # Provide a typed request attribute for mixin users (APIView sets this at runtime)
    request: Optional[Request] = None
    
    def _studio_base_url(self) -> str:
        """
        Determine the Studio base URL from settings or environment with sensible fallbacks.
        """
        # Preferred explicit setting
        studio_base = getattr(settings, 'STUDIO_BASE_URL', None)
        if not studio_base:
            # Common Open edX setting for Studio host
            studio_base = getattr(settings, 'CMS_BASE', None) or getattr(settings, 'STUDIO_BASE', None)
        if not studio_base:
            studio_base = os.environ.get('STUDIO_BASE_URL') or os.environ.get('CMS_BASE')

        if not studio_base:
            return ''

        # Ensure scheme
        if not studio_base.startswith('http://') and not studio_base.startswith('https://'):
            # Prefer https if cookies are secure, else http
            use_https = getattr(settings, 'SESSION_COOKIE_SECURE', False)
            scheme = 'https' if use_https else 'http'
            studio_base = f"{scheme}://{studio_base}"
        return studio_base

    def _get_cms_data(self, cms_path, request_method='GET', data=None):
        """
        Fetch data from CMS contentstore API.
        """
        # Determine the Studio/Studio API base and return early if missing.
        studio_base = self._studio_base_url()
        if not studio_base:
            LOGGER.error('Studio base URL not configured (set STUDIO_BASE_URL or CMS_BASE)')
            return False, 'CMS not configured', 500

        url = f"{studio_base.rstrip('/')}/{cms_path.lstrip('/')}"
        LOGGER.info(f'Fetching from CMS: {request_method} {url}')
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Forward authentication headers
        req = getattr(self, 'request', None)
        if req is not None:
            if 'HTTP_AUTHORIZATION' in req.META:
                headers['Authorization'] = req.META['HTTP_AUTHORIZATION']
            if 'HTTP_USE_JWT_COOKIE' in req.META:
                headers['USE-JWT-COOKIE'] = req.META['HTTP_USE_JWT_COOKIE']
            if 'HTTP_X_REQUESTED_WITH' in req.META:
                headers['X-Requested-With'] = req.META['HTTP_X_REQUESTED_WITH']

        # Forward cookies
        cookies = getattr(req, 'COOKIES', {}) if req is not None else {}
        
        try:
            resp = requests.request(
                method=request_method,
                url=url,
                headers=headers,
                json=data if data and request_method != 'GET' else None,
                cookies=cookies,
                timeout=10,
                allow_redirects=False,
            )
            
            LOGGER.info(f'CMS responded with status {resp.status_code}')
            if resp.status_code >= 400:
                LOGGER.warning(f'CMS error response: {resp.text[:500]}')
                
            try:
                response_data = resp.json() if resp.content else {}
            except ValueError:
                response_data = {'error': 'Invalid JSON response from CMS', 'raw_response': resp.text[:200]}
                
            return resp.status_code < 400, response_data, resp.status_code
            
        except requests.RequestException as e:
            LOGGER.exception(f'Error connecting to CMS: {e}')
            return False, f'CMS connection failed: {str(e)}', 502


def _normalize_storage_url(upload_url: Optional[str], file_path: Optional[str]) -> Optional[str]:
    """Normalize storage URLs to avoid duplicated bucket segments and ensure absolute URLs.

    Handles cases where the storage key accidentally includes the bucket name (e.g.,
    ROOT_PATH == bucket), which can lead to URLs like /bucket/bucket/key.

    If upload_url is missing or clearly malformed, attempts to rebuild a correct URL from
    file_path and S3 settings.
    """
    try:
        if not upload_url and not file_path:
            return upload_url

        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') or ''
        endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', '') or ''

        # Choose protocol from HTTPS setting
        https_setting = getattr(settings, 'HTTPS', False)
        if isinstance(https_setting, str):
            protocol = 'https' if https_setting.lower() not in ('off', 'false', '0') else 'http'
        else:
            protocol = 'https' if https_setting else 'http'

        def build_from_key(key: str) -> Optional[str]:
            if not key:
                return None
            # Strip any accidental leading bucket prefix from key
            if bucket and (key.startswith(f"{bucket}/")):
                key = key[len(bucket) + 1:]
            # Encode path but preserve slashes
            enc_key = urllib.parse.quote(key, safe='/')
            if endpoint:
                ep = endpoint.replace('https://', '').replace('http://', '').strip('/')
                return f"{protocol}://{ep}/{bucket}/{enc_key}" if bucket else f"{protocol}://{ep}/{enc_key}"
            # Fallback to MEDIA_URL or LMS_BASE
            media_url = getattr(settings, 'MEDIA_URL', '') or ''
            if media_url.startswith('http://') or media_url.startswith('https://'):
                return f"{media_url.rstrip('/')}/{enc_key}"
            lms_base = getattr(settings, 'LMS_BASE', '') or ''
            if lms_base:
                base = lms_base.rstrip('/')
                # Assume media served at /media
                return f"{base}/media/{enc_key}"
            return f"/media/{enc_key}"

        # If we have a URL, try to fix duplicate bucket segments like /bucket/bucket/
        if upload_url:
            fixed = upload_url
            if bucket:
                double = f"/{bucket}/{bucket}/"
                single = f"/{bucket}/"
                if double in fixed:
                    fixed = fixed.replace(double, single)
            # If URL lacks scheme but starts with '/', prefix LMS_BASE
            if fixed.startswith('/') and not fixed.startswith('//'):
                lms_base = getattr(settings, 'LMS_BASE', '') or ''
                if lms_base:
                    fixed = f"{lms_base.rstrip('/')}{fixed}"
            # If still no scheme, try building from file_path
            if not fixed.startswith('http://') and not fixed.startswith('https://'):
                rebuilt = build_from_key(file_path or '')
                return rebuilt or fixed
            return fixed

        # No upload_url present: build from file_path
        return build_from_key(file_path or '')
    except Exception:  # pragma: no cover - defensive
        return upload_url or None


def _presign_get_url(file_path: Optional[str]) -> Optional[str]:
    """Generate a presigned GET URL for the object key (file_path) in the configured bucket.

    Returns None if presigning cannot be performed.
    """
    if not file_path:
        return None
    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    if not bucket:
        return None
    s3_client = boto3.client(
        's3',
        endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
        aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
        aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
    )
    params = {'Bucket': bucket, 'Key': file_path}
    # Best effort: set inline viewing for PDFs and common types
    try:
        _, ext = os.path.splitext(file_path)
        ext = (ext or '').lower()
        if ext in ['.pdf']:
            params['ResponseContentType'] = 'application/pdf'
            params['ResponseContentDisposition'] = f'inline; filename="{os.path.basename(file_path)}"'
    except Exception:
        pass
    try:
        return s3_client.generate_presigned_url('get_object', Params=params, ExpiresIn=3600)
    except Exception:
        return None


def _get_child_category(child) -> Optional[str]:
    """Robustly determine the category/type of a modulestore child block.

    This checks multiple attributes and falls back to class-name heuristics so that
    'problem' blocks (quizzes) are detected consistently across modulestore variants.
    """
    try:
        # Prefer explicit category on the block
        cat = getattr(child, 'category', None)
        if cat:
            return cat

        # Some blocks expose type on the location object as block_type
        loc = getattr(child, 'location', None)
        if loc is not None:
            bt = getattr(loc, 'block_type', None)
            if bt:
                return bt

        # Fallback: use class name
        cname = getattr(child, '__class__', None)
        if cname:
            name = cname.__name__.lower()
            if 'problem' in name or 'question' in name or 'quiz' in name:
                return 'problem'
            if 'video' in name:
                return 'video'
            if 'html' in name or 'slide' in name:
                return 'html'

        return None
    except Exception:
        return None


@view_auth_classes(is_authenticated=True)
class UnitMediaListView(DeveloperErrorViewMixin, APIView, CMSProxyMixin):
    """
    Read-only view for listing unit media files.
    Mirrors CMS UnitMediaListView but only supports GET operations.
    """
    
    def get(self, request: Request, unit_id: str, media_type: str):
        """
        Get list of media files for a unit.
        
        **Example Request**
            GET /api/course_home/v1/content/units/{unit_id}/{media_type}s/
        """
        self.request = request  # Store for CMSProxyMixin


        # Validate media type (plural)
        if media_type not in ['videos', 'slides', 'quizzes']:
            return Response(
                {'error': 'Invalid media type. Must be "videos", "slides", or "quizzes".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Access control and unit lookup
            try:
                decoded_unit_id = urllib.parse.unquote(unit_id)
                usage_key = UsageKey.from_string(decoded_unit_id)
                course_key = usage_key.context_key
                course_overview = CourseOverview.get_from_id(course_key)
            except (InvalidKeyError, CourseOverview.DoesNotExist):
                return Response({'error': 'Invalid unit_id or course not found'}, status=status.HTTP_404_NOT_FOUND)

            if not has_access(request.user, 'load', course_overview):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # Check if this is a final evaluation unit - do this BEFORE fetching media
            is_final_evaluation = False
            try:
                store = modulestore()
                is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                                bool(has_access(request.user, 'instructor', course_overview))
                branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
                with store.branch_setting(branch):
                    vertical = store.get_item(usage_key)
                    display_name = getattr(vertical, 'display_name', '').strip().lower()
                    # Check if the display name matches final evaluation variants
                    final_eval_variants = ['kiểm tra cuối khoá', 'kiểm tra cuối khóa', 'kiem tra cuoi khoa']
                    if any(variant in display_name for variant in final_eval_variants):
                        LOGGER.info(f"Detected final evaluation vertical in media list: {getattr(vertical, 'display_name', '')}")
                        # Check if course has final evaluation configured
                        try:
                            # Use the modulestore-backed CourseDetails to avoid importing CMS models
                            from openedx.core.djangoapps.models.course_details import CourseDetails as ModulestoreCourseDetails
                            course_details = ModulestoreCourseDetails.fetch(course_key)
                            evaluation_type = getattr(course_details, 'final_evaluation_type', None)
                            if evaluation_type:
                                is_final_evaluation = True
                                LOGGER.info(f"Final evaluation type in media list: {evaluation_type}")
                        except Exception as e:
                            LOGGER.warning(f"Could not check final evaluation type via modulestore CourseDetails: {e}")
                            is_final_evaluation = False
            except Exception as e:
                LOGGER.warning(f"Could not check if unit is final evaluation: {e}")
                is_final_evaluation = False

            # If this is a final evaluation and media_type is videos or slides, return empty list immediately
            if is_final_evaluation and media_type in ['videos', 'slides']:
                LOGGER.info(f"Returning empty {media_type} list for final evaluation unit {unit_id}")
                return Response({media_type: []})

            # Start with DB-backed media (UnitMediaFile) if available
            db_items = []
            if CMSUnitMediaFile:
                # Use DB-backed media (UnitMediaFile) when available
                
                if media_type in ['videos', 'slides']:
                    singular_type = 'video' if media_type == 'videos' else 'slide'
                    try:
                        # Try decoded unit id first, then fallbacks for encoded/raw ids
                        qs = CMSUnitMediaFile.get_unit_media(decoded_unit_id, singular_type)
                        if not qs.exists() and unit_id != decoded_unit_id:
                            qs = CMSUnitMediaFile.get_unit_media(unit_id, singular_type)
                        if not qs.exists():
                            encoded_id = urllib.parse.quote(decoded_unit_id, safe=':/@+')
                            if encoded_id != decoded_unit_id and encoded_id != unit_id:
                                qs = CMSUnitMediaFile.get_unit_media(encoded_id, singular_type)

                        for mf in qs:
                            
                            # Safely resolve uploader username when available
                            uploader_username = None
                            try:
                                uploader = getattr(mf, 'uploaded_by', None)
                                if uploader is not None:
                                    uploader_username = getattr(uploader, 'username', None)
                            except Exception:
                                uploader_username = None

                            # For YouTube videos, use the stored URLs directly from DB
                            # For file uploads, use presigned/normalized URLs
                            public_url = getattr(mf, 'public_url', None)
                            url = getattr(mf, 'url', None) 
                            upload_url = getattr(mf, 'upload_url', None)
                            file_path = getattr(mf, 'file_path', None)
                            file_type = getattr(mf, 'file_type', None)
                            external_url = getattr(mf, 'external_url', None)
                            file_name = getattr(mf, 'file_name', None)
                            
                            # Initialize youtube_id to None so it's always defined
                            youtube_id = None
                            
                            # Special handling for external videos (YouTube) that don't have URLs stored
                            youtube_id = None
                            if file_type == 'video/external' and not (public_url or url):
                                # Method 1: Extract from external_url
                                if external_url:
                                    youtube_id = extract_youtube_id(external_url)

                                # Method 2: Extract from file_name if necessary
                                if not youtube_id and file_name and ('.url' in file_name.lower() or 'youtube' in file_name.lower()):
                                    import re
                                    match = re.search(r'[a-zA-Z0-9_-]{11}', file_name)
                                    if match:
                                        youtube_id = match.group(0)

                                # Method 3: Try XBlock metadata fallback
                                if not youtube_id:
                                    try:
                                        store = modulestore()
                                        unit_usage_key = UsageKey.from_string(decoded_unit_id)

                                        # Use appropriate branch
                                        is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                                                        bool(has_access(request.user, 'instructor', course_overview))
                                        branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only

                                        with store.branch_setting(branch):
                                            try:
                                                vertical = store.get_item(unit_usage_key)
                                                LOGGER.info(f"[DEBUG] Searching XBlocks in vertical {unit_usage_key} for YouTube ID")

                                                for child_key in getattr(vertical, 'children', []) or []:
                                                    try:
                                                        child = store.get_item(child_key)
                                                        child_category = _get_child_category(child)
                                                        LOGGER.info(f"[DEBUG] Checking child {child_key}, category: {child_category}")

                                                        if child_category == 'video':
                                                            # Check all possible YouTube ID fields
                                                            for youtube_field in ['youtube_id_1_0', 'youtube_id', 'youtube']:
                                                                try:
                                                                    # Try metadata first, then attribute
                                                                    md = getattr(child, 'metadata', {}) or {}
                                                                    video_youtube_id = md.get(youtube_field) or getattr(child, youtube_field, None)
                                                                    if video_youtube_id:
                                                                        youtube_id = video_youtube_id
                                                                        LOGGER.info(f"[DEBUG] Found YouTube ID from XBlock {child_key}.{youtube_field}: {youtube_id}")
                                                                        break
                                                                except Exception:
                                                                    # If modulestore lookup fails at any nested point, continue to next field
                                                                    continue

                                                            # If we found a youtube_id, generate URLs
                                                            if youtube_id and not (public_url or url):
                                                                public_url = f"https://www.youtube.com/embed/{youtube_id}"
                                                                url = f"https://www.youtube.com/watch?v={youtube_id}"

                                                    except Exception:
                                                        # Skip problematic child entries
                                                        continue
                                            except Exception:
                                                # modulestore lookup failed; continue without XBlock fallback
                                                pass
                                    except Exception:
                                        # modulestore setup failed; ignore XBlock fallback
                                        pass

                                if youtube_id:
                                    public_url = f"https://www.youtube.com/embed/{youtube_id}"
                                    url = f"https://www.youtube.com/watch?v={youtube_id}"
                                    LOGGER.info(f"[DEBUG] Generated YouTube URLs for {mf.id}: youtube_id={youtube_id}, public_url={public_url}")
                            
                            # Prioritize generated YouTube URLs for external videos
                            if youtube_id and file_type == 'video/external':
                                final_public_url = f"https://www.youtube.com/embed/{youtube_id}"
                                final_url = f"https://www.youtube.com/watch?v={youtube_id}"
                                final_download_url = final_url
                                final_upload_url = final_public_url
                                LOGGER.info(f"[DEBUG] Using generated YouTube URLs for external video {mf.id}")
                            # If we have explicit public_url or url (YouTube videos), use them directly
                            elif public_url or url:
                                final_public_url = public_url
                                final_url = url
                                final_download_url = url or public_url
                                final_upload_url = public_url or upload_url
                            else:
                                # For file uploads, use presigned/normalized approach
                                presigned = _presign_get_url(file_path)
                                normalized_url = presigned or _normalize_storage_url(upload_url, file_path)
                                final_public_url = normalized_url
                                final_url = normalized_url
                                final_download_url = normalized_url
                                final_upload_url = normalized_url

                            base = {
                                'id': str(mf.id),
                                'title': mf.display_name or mf.file_name,
                                'displayName': mf.display_name or mf.file_name,
                                'fileName': mf.file_name,
                                'fileType': mf.file_type,
                                'size': mf.file_size,
                                'uploadedByUsername': uploader_username,
                                # Provide multiple URL fields for consumer flexibility
                                'url': final_url,
                                'publicUrl': final_public_url,
                                'downloadUrl': final_download_url,
                                'uploadUrl': final_upload_url,
                            }
                            if singular_type == 'video':
                                # Learning MFE looks for videoUrl/url/downloadUrl
                                base['videoUrl'] = final_url
                            else:
                                # Slides: prefer fileUrl
                                base['fileUrl'] = final_url
                            db_items.append(base)
                    except Exception as db_err:  # pragma: no cover - defensive
                        LOGGER.warning(f"DB unit media lookup failed for unit {decoded_unit_id}: {db_err}")
                elif media_type == 'quizzes':
                    # Return DB-backed Chalix quizzes attached at subsection or unit level
                    try:
                        if CMSChalixQuiz:
                            # Determine candidate parent locators: unit itself and its parent (subsection)
                            candidate_locators = set()
                            candidate_locators.add(decoded_unit_id)

                            # Attempt to resolve parent sequential locator to match authoring semantics
                            try:
                                store = modulestore()
                                is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                                                bool(has_access(request.user, 'instructor', course_overview))
                                branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
                                with store.branch_setting(branch):
                                    parent_loc = store.get_parent_location(usage_key)
                                if parent_loc:
                                    candidate_locators.add(str(parent_loc))
                            except Exception:
                                pass

                            # Query active quizzes for this course under any of the candidate parent locators
                            LOGGER.info(f"Querying quizzes for course_key={course_key}, parent_locator__in={list(candidate_locators)}")
                            qs = CMSChalixQuiz.objects.filter(
                                course_key=course_key,
                                is_active=True,
                                parent_locator__in=list(candidate_locators),
                            ).order_by('-created_at')
                            LOGGER.info(f"Found {qs.count()} quizzes")

                            for q in qs:
                                try:
                                    question_count = getattr(q, 'question_count', None)
                                except Exception:
                                    question_count = None
                                db_items.append({
                                    'id': str(q.pk),
                                    'title': q.title,
                                    'questionCount': question_count,
                                })
                    except Exception as db_err:
                        LOGGER.warning(f"DB chalix quiz lookup failed for unit {decoded_unit_id}: {db_err}")


            # Also traverse modulestore to include XBlock-based media
            store = modulestore()
            is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                            bool(has_access(request.user, 'instructor', course_overview))
            branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
            try:
                with store.branch_setting(branch):
                    vertical = store.get_item(usage_key)
            except ItemNotFoundError:
                vertical = None

            videos, slides, quizzes = [], [], []

            if vertical is not None:
                with store.branch_setting(branch):
                    for child_key in getattr(vertical, 'children', []) or []:
                        try:
                            child = store.get_item(child_key)
                        except ItemNotFoundError:
                            continue
                        except Exception as child_err:
                            # Log and skip problematic children to avoid 500 errors
                            LOGGER.warning(f"Failed to load child {child_key}: {child_err}")
                            continue

                        try:
                            cat = _get_child_category(child)
                            md = getattr(child, 'metadata', {}) or {}
                            title = getattr(child, 'display_name', '')
                        except Exception as metadata_err:
                            # Skip children with metadata access issues
                            LOGGER.warning(f"Failed to access metadata for child {child_key}: {metadata_err}")
                            continue

                        if cat == 'video':
                            try:
                                youtube_id = md.get('youtube_id_1_0') or getattr(child, 'youtube_id_1_0', '')
                                video_url = md.get('video_url') or getattr(child, 'video_url', '')
                                edx_video_id = md.get('edx_video_id') or getattr(child, 'edx_video_id', '')
                                
                                # Build YouTube URLs if we have a YouTube ID
                                public_url = None
                                watch_url = None
                                if youtube_id:
                                    public_url = f"https://www.youtube.com/embed/{youtube_id}"
                                    watch_url = f"https://www.youtube.com/watch?v={youtube_id}"
                                
                                videos.append({
                                    'id': str(getattr(child, 'location', '')),
                                    'title': title,
                                    'youtubeId': youtube_id,
                                    'videoUrl': video_url or watch_url or '',
                                    'edxVideoId': edx_video_id,
                                    # Add the missing URL fields that frontend expects
                                    'url': watch_url,
                                    'publicUrl': public_url,
                                    'downloadUrl': watch_url,
                                    'uploadUrl': public_url,
                                })
                            except Exception as video_err:
                                LOGGER.warning(f"Failed to serialize video XBlock {child_key}: {video_err}")
                                continue
                        elif cat == 'html':
                            try:
                                file_url = md.get('file_url')
                                slides.append({
                                    'id': str(getattr(child, 'location', '')),
                                    'title': title,
                                    'fileUrl': file_url,
                                    'fileType': md.get('file_type') or ('html' if not file_url else 'pdf'),
                                })
                            except Exception as slide_err:
                                LOGGER.warning(f"Failed to serialize slide XBlock {child_key}: {slide_err}")
                                continue
                        elif cat == 'problem':
                            try:
                                # Always provide questionCount as int (default 1 if missing)
                                qcount = md.get('question_count')
                                try:
                                    qcount = int(qcount) if qcount is not None else 1
                                except Exception:
                                    qcount = 1
                                quizzes.append({
                                    'id': str(getattr(child, 'location', '')),
                                    'title': title,
                                    'questionCount': qcount,
                                })
                            except Exception as quiz_err:
                                LOGGER.warning(f"Failed to serialize quiz XBlock {child_key}: {quiz_err}")
                                continue
                if not quizzes:
                    child_locs = []
                    for ck in getattr(vertical, 'children', []) or []:
                        try:
                            it = store.get_item(ck)
                            loc = getattr(it, 'location', None)
                            if loc is not None:
                                child_locs.append(str(loc))
                        except Exception:
                            continue
                    LOGGER.info(f"No quizzes found in vertical {getattr(vertical, 'location', None)} children: {child_locs}")

            # Merge DB items with modulestore-derived ones for all media types
            result_map = {
                'videos': db_items + videos,
                'slides': db_items + slides,
                'quizzes': db_items + quizzes,
            }
            return Response(result_map[media_type], status=status.HTTP_200_OK)

        except Exception as e:
            LOGGER.exception(f"Error listing unit media files: {str(e)}")
            return Response({'error': 'Failed to retrieve media files'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
class UnitMediaDetailView(DeveloperErrorViewMixin, APIView, CMSProxyMixin):
    """
    Read-only view for individual unit media file details.
    Mirrors CMS UnitMediaDetailView but only supports GET operations.
    """
    
    def get(self, request: Request, unit_id: str, media_type: str, media_id: str):
        """
        Get details of a specific media file.
        
        **Example Request**
            GET /api/course_home/v1/content/units/{unit_id}/{media_type}s/{media_id}/
        """
        self.request = request  # Store for CMSProxyMixin

        try:
            # Access control
            try:
                decoded_unit_id = urllib.parse.unquote(unit_id)
                usage_key = UsageKey.from_string(decoded_unit_id)
                course_key = usage_key.context_key
                course_overview = CourseOverview.get_from_id(course_key)
            except (InvalidKeyError, CourseOverview.DoesNotExist):
                return Response({'error': 'Invalid unit_id or course not found'}, status=status.HTTP_404_NOT_FOUND)

            if not has_access(request.user, 'load', course_overview):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # First try DB-backed UnitMediaFile if applicable
            if CMSUnitMediaFile and media_type in ['video', 'slide']:
                try:
                    mf = CMSUnitMediaFile.objects.get(id=media_id, unit_id=decoded_unit_id, media_type=media_type)
                    
                    # For YouTube videos, use the stored URLs directly from DB
                    # For file uploads, use presigned/normalized URLs
                    public_url = getattr(mf, 'public_url', None)
                    url = getattr(mf, 'url', None) 
                    upload_url = getattr(mf, 'upload_url', None)
                    file_path = getattr(mf, 'file_path', None)
                    
                    # If we have explicit public_url or url (YouTube videos), use them directly
                    if public_url or url:
                        final_public_url = public_url
                        final_url = url
                        final_download_url = url or public_url
                        final_upload_url = public_url or upload_url
                    else:
                        # For file uploads, use presigned/normalized approach
                        presigned = _presign_get_url(file_path)
                        normalized_url = presigned or _normalize_storage_url(upload_url, file_path)
                        final_public_url = normalized_url
                        final_url = normalized_url
                        final_download_url = normalized_url
                        final_upload_url = normalized_url
                    
                    data = {
                        'id': str(mf.id),
                        'title': mf.display_name or mf.file_name,
                        'displayName': mf.display_name or mf.file_name,
                        'fileName': mf.file_name,
                        'fileType': mf.file_type,
                        'size': mf.file_size,
                        'url': final_url,
                        'publicUrl': final_public_url,
                        'downloadUrl': final_download_url,
                        'uploadUrl': final_upload_url,
                    }
                    if media_type == 'video':
                        data['videoUrl'] = final_url
                    else:
                        data['fileUrl'] = final_url
                    return Response(data, status=status.HTTP_200_OK)
                except CMSUnitMediaFile.DoesNotExist:
                    pass
                except Exception as db_err:  # pragma: no cover
                    LOGGER.warning(f"DB unit media detail lookup failed: {db_err}")

            # Fallback to modulestore XBlock child lookup
            store = modulestore()
            is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                            bool(has_access(request.user, 'instructor', course_overview))
            branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
            try:
                with store.branch_setting(branch):
                    vertical = store.get_item(usage_key)
            except ItemNotFoundError:
                return Response({'error': 'Unit not found'}, status=status.HTTP_404_NOT_FOUND)

            # Normalize media_type to plural for comparison
            plural = {'video': 'videos', 'slide': 'slides', 'quiz': 'quizzes'}.get(media_type, f'{media_type}s')

            def serialize_child(child):
                cat = _get_child_category(child)
                md = getattr(child, 'metadata', {}) or {}
                title = getattr(child, 'display_name', '')
                if plural == 'videos' and cat == 'video':
                    return {
                        'id': str(getattr(child, 'location', '')),
                        'title': title,
                        'youtubeId': md.get('youtube_id_1_0') or getattr(child, 'youtube_id_1_0', ''),
                        'videoUrl': md.get('video_url') or getattr(child, 'video_url', ''),
                    }
                if plural == 'slides' and cat == 'html':
                    file_url = md.get('file_url')
                    return {
                        'id': str(getattr(child, 'location', '')),
                        'title': title,
                        'fileUrl': file_url,
                        'fileType': md.get('file_type') or ('html' if not file_url else 'pdf'),
                    }
                if plural == 'quizzes' and cat == 'problem':
                    return {
                        'id': str(getattr(child, 'location', '')),
                        'title': title,
                        'questionCount': md.get('question_count'),
                    }
                return None

            with store.branch_setting(branch):
                for child_key in getattr(vertical, 'children', []) or []:
                    try:
                        child = store.get_item(child_key)
                    except ItemNotFoundError:
                        continue
                    if str(getattr(child, 'location', '')) == media_id:
                        data = serialize_child(child)
                        if data is not None:
                            return Response(data, status=status.HTTP_200_OK)
            return Response({'error': 'Media not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            LOGGER.exception(f"Error retrieving unit media file: {str(e)}")
            return Response({'error': 'Failed to retrieve media file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
class UnitMediaStatsView(DeveloperErrorViewMixin, APIView, CMSProxyMixin):
    """
    Read-only view for unit media statistics.
    Mirrors CMS UnitMediaStatsView but only supports GET operations.
    """
    
    def get(self, request: Request, unit_id: str):
        """
        Get statistics for all media files in a unit.
        
        **Example Request**
            GET /api/course_home/v1/content/units/{unit_id}/media/stats/
        """
        self.request = request  # Store for CMSProxyMixin

        try:
            # Access control
            try:
                decoded_unit_id = urllib.parse.unquote(unit_id)
                usage_key = UsageKey.from_string(decoded_unit_id)
                course_key = usage_key.context_key
                course_overview = CourseOverview.get_from_id(course_key)
            except (InvalidKeyError, CourseOverview.DoesNotExist):
                return Response({'error': 'Invalid unit_id or course not found'}, status=status.HTTP_404_NOT_FOUND)

            if not has_access(request.user, 'load', course_overview):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # Initialize totals
            totals = {
                'unitId': urllib.parse.unquote(unit_id),
                'totalFiles': 0,
                'totalVideos': 0,
                'totalSlides': 0,
                'totalSizeBytes': 0,
            }

            # Include DB-backed counts if available (try multiple unit_id forms)
            if CMSUnitMediaFile:
                try:
                    vids_qs = CMSUnitMediaFile.get_unit_media(decoded_unit_id, 'video')
                    slds_qs = CMSUnitMediaFile.get_unit_media(decoded_unit_id, 'slide')
                    if not vids_qs.exists() and unit_id != decoded_unit_id:
                        vids_qs = CMSUnitMediaFile.get_unit_media(unit_id, 'video')
                    if not slds_qs.exists() and unit_id != decoded_unit_id:
                        slds_qs = CMSUnitMediaFile.get_unit_media(unit_id, 'slide')
                    if not vids_qs.exists() or not slds_qs.exists():
                        encoded_id = urllib.parse.quote(decoded_unit_id, safe=':/@+')
                        if not vids_qs.exists():
                            vids_qs = CMSUnitMediaFile.get_unit_media(encoded_id, 'video')
                        if not slds_qs.exists():
                            slds_qs = CMSUnitMediaFile.get_unit_media(encoded_id, 'slide')
                    totals['totalVideos'] += vids_qs.count()
                    totals['totalSlides'] += slds_qs.count()
                    totals['totalFiles'] += totals['totalVideos'] + totals['totalSlides']
                    totals['totalSizeBytes'] += sum((mf.file_size or 0) for mf in vids_qs) + \
                                                sum((mf.file_size or 0) for mf in slds_qs)
                except Exception as db_err:  # pragma: no cover
                    LOGGER.warning(f"DB unit media stats failed for unit {decoded_unit_id}: {db_err}")

            # Also include modulestore-based media counts
            store = modulestore()
            is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                            bool(has_access(request.user, 'instructor', course_overview))
            branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
            try:
                with store.branch_setting(branch):
                    vertical = store.get_item(usage_key)
            except ItemNotFoundError:
                vertical = None

            if vertical is not None:
                with store.branch_setting(branch):
                    for child_key in getattr(vertical, 'children', []) or []:
                        try:
                            child = store.get_item(child_key)
                        except ItemNotFoundError:
                            continue
                        cat = _get_child_category(child)
                        if cat == 'video':
                            totals['totalVideos'] += 1
                            totals['totalFiles'] += 1
                        elif cat == 'html':
                            totals['totalSlides'] += 1
                            totals['totalFiles'] += 1
                        elif cat == 'problem':
                            totals['totalFiles'] += 1

            return Response(totals, status=status.HTTP_200_OK)

        except Exception as e:
            LOGGER.exception(f"Error retrieving unit media stats: {str(e)}")
            return Response({'error': 'Failed to retrieve media statistics'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
class ContainerHandlerView(DeveloperErrorViewMixin, APIView, CMSProxyMixin):
    """
    Read-only view for container/vertical data.
    Mirrors CMS ContainerHandlerView but only supports GET operations.
    """
    
    def get(self, request: Request, unit_id: str):
        """
        Get container/vertical data for a unit.
        
        **Example Request**
            GET /api/course_home/v1/content/container_handler/{unit_id}/
        """
        self.request = request  # Store for CMSProxyMixin

        try:
            # Access control
            try:
                decoded_unit_id = urllib.parse.unquote(unit_id)
                usage_key = UsageKey.from_string(decoded_unit_id)
                course_key = usage_key.context_key
                course_overview = CourseOverview.get_from_id(course_key)
            except (InvalidKeyError, CourseOverview.DoesNotExist):
                return Response({'error': 'Invalid unit_id or course not found'}, status=status.HTTP_404_NOT_FOUND)

            if not has_access(request.user, 'load', course_overview):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # LMS-native: return a minimal container descriptor compatible with MFE usage
            store = modulestore()
            # Choose branch: staff/instructors see draft-preferred similar to Studio; learners see published-only
            is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                            bool(has_access(request.user, 'instructor', course_overview))
            branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
            try:
                with store.branch_setting(branch):
                    container = store.get_item(usage_key)
            except ItemNotFoundError:
                return Response({'error': 'Container not found'}, status=status.HTTP_404_NOT_FOUND)

            def child_info(child):
                # Minimal child info used by the MFE
                return {
                    'id': str(getattr(child, 'location', '')),
                    'category': _get_child_category(child),
                    'display_name': getattr(child, 'display_name', ''),
                }

            children = []
            debug_children = []
            request_debug = str(getattr(request, 'GET', {})).lower()
            debug_enabled = False
            # Support explicit ?debug=1 or ?debug=true
            try:
                q = request.GET.get('debug', '')
                if q and str(q).lower() in ('1', 'true', 'yes'):
                    debug_enabled = True
            except Exception:
                debug_enabled = False

            # Check if this is a final evaluation vertical - if so, filter out videos and slides
            is_final_evaluation = False
            if hasattr(container, 'display_name'):
                display_name_lower = container.display_name.lower().strip()
                final_eval_variants = [
                    "kiểm tra cuối khoá",
                    "kiểm tra cuối khóa", 
                    "kiem tra cuoi khoa",
                ]
                is_final_evaluation = any(variant in display_name_lower for variant in final_eval_variants)
                
                if is_final_evaluation:
                    LOGGER.info(f"Detected final evaluation vertical: {container.display_name}")
                    # Check if there's a final evaluation configured
                    try:
                        # Use modulestore-backed CourseDetails to avoid importing CMS models into LMS process
                        from openedx.core.djangoapps.models.course_details import CourseDetails
                        course_details = CourseDetails.fetch(course_key)
                        evaluation_type = getattr(course_details, 'final_evaluation_type', None)
                        LOGGER.info(f"Final evaluation type: {evaluation_type}")
                        # Only filter if there's an actual evaluation configured
                        if not evaluation_type:
                            is_final_evaluation = False
                    except Exception as e:
                        LOGGER.warning(f"Could not check final evaluation type via CourseDetails.fetch: {e}")
                        is_final_evaluation = False

            with store.branch_setting(branch):
                for ck in getattr(container, 'children', []) or []:
                    try:
                        ch = store.get_item(ck)
                    except ItemNotFoundError:
                        continue
                    except Exception as child_err:
                        LOGGER.warning(f"Failed to load container child {ck}: {child_err}")
                        continue
                    try:
                        child_category = _get_child_category(ch)
                        
                        # Skip video and slide (including HTML-based slides) children if this is a final evaluation
                        if is_final_evaluation and child_category in ('video', 'slide', 'html'):
                            LOGGER.info(f"Filtering out {child_category} from final evaluation: {getattr(ch, 'display_name', '')}")
                            continue
                        
                        children.append(child_info(ch))
                        if debug_enabled:
                            # Provide extra diagnostics about the child to help map categories
                            metadata = getattr(ch, 'metadata', {}) or {}
                            loc = getattr(ch, 'location', None)
                            block_type = getattr(loc, 'block_type', None) if loc is not None else None
                            debug_children.append({
                                'id': str(loc) if loc is not None else str(getattr(ch, 'id', '')),
                                'category': child_category,
                                'class': type(ch).__name__,
                                'block_type': block_type,
                                'display_name': getattr(ch, 'display_name', ''),
                                'metadata_keys': list(metadata.keys()),
                            })
                    except Exception as info_err:
                        LOGGER.warning(f"Failed to get info for container child {ck}: {info_err}")
                        if debug_enabled:
                            debug_children.append({
                                'id': str(ck),
                                'error': f'Failed to serialize: {str(info_err)}',
                            })
                        continue

            # Also add ChalixQuiz objects as virtual children (skip for final evaluation units)
            try:
                if CMSChalixQuiz and not is_final_evaluation:
                    # Look for quizzes attached to this unit or its parent
                    parent_locators = [str(usage_key)]
                    try:
                        parent_location = store.get_parent_location(usage_key)
                        if parent_location:
                            parent_locators.append(str(parent_location))
                    except Exception:
                        pass
                    
                    # Query active quizzes for this course under any of the candidate parent locators
                    quiz_qs = CMSChalixQuiz.objects.filter(
                        course_key=course_key,
                        is_active=True,
                        parent_locator__in=parent_locators
                    ).order_by('-created_at')
                    
                    for quiz in quiz_qs[:10]:  # Limit to prevent excessive results
                        quiz_child = {
                            'id': f'chalix-quiz-{quiz.id}',
                            'category': 'problem',  # Map to 'problem' so MFE filters it as a quiz
                            'display_name': quiz.title,
                        }
                        children.append(quiz_child)
                        
                        if debug_enabled:
                            debug_children.append({
                                'id': f'chalix-quiz-{quiz.id}',
                                'category': 'problem',
                                'class': 'ChalixQuiz',
                                'block_type': 'chalix_quiz',
                                'display_name': quiz.title,
                                'metadata_keys': ['course_key', 'parent_locator', 'title', 'description'],
                            })
                elif is_final_evaluation:
                    LOGGER.info(f"Skipping ChalixQuiz objects for final evaluation unit {decoded_unit_id}")
                            
            except Exception as quiz_err:
                LOGGER.warning(f"Failed to load ChalixQuiz objects for unit {decoded_unit_id}: {quiz_err}")
                if debug_enabled:
                    debug_children.append({
                        'error': f'ChalixQuiz lookup failed: {str(quiz_err)}',
                        'CMSChalixQuiz_available': CMSChalixQuiz is not None,
                    })

            data = {
                'xblock_info': {
                    'id': str(getattr(container, 'location', '')),
                    'category': _get_child_category(container) or getattr(container, 'category', None),
                    'display_name': getattr(container, 'display_name', ''),
                    'children': children,
                }
            }
            if debug_enabled:
                data['debug_children'] = debug_children
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            LOGGER.exception(f"Error retrieving container data: {str(e)}")
            return Response({'error': 'Failed to retrieve container data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
class VerticalContainerView(DeveloperErrorViewMixin, APIView, CMSProxyMixin):
    """
    Read-only view for vertical container children.
    Mirrors CMS VerticalContainerView but only supports GET operations.
    """
    
    def get(self, request: Request, unit_id: str):
        """
        Get children of a vertical container.
        
        **Example Request**
            GET /api/course_home/v1/content/container/vertical/{unit_id}/children/
        """
        self.request = request  # Store for CMSProxyMixin

        try:
            # Access control
            try:
                decoded_unit_id = urllib.parse.unquote(unit_id)
                usage_key = UsageKey.from_string(decoded_unit_id)
                course_key = usage_key.context_key
                course_overview = CourseOverview.get_from_id(course_key)
            except (InvalidKeyError, CourseOverview.DoesNotExist):
                return Response({'error': 'Invalid unit_id or course not found'}, status=status.HTTP_404_NOT_FOUND)

            if not has_access(request.user, 'load', course_overview):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            # LMS-native: return children of the vertical container
            store = modulestore()
            is_staff_view = bool(has_access(request.user, 'staff', course_overview)) or \
                            bool(has_access(request.user, 'instructor', course_overview))
            branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
            try:
                with store.branch_setting(branch):
                    vertical = store.get_item(usage_key)
            except ItemNotFoundError:
                return Response({'error': 'Vertical not found'}, status=status.HTTP_404_NOT_FOUND)

            children = []
            with store.branch_setting(branch):
                for ck in getattr(vertical, 'children', []) or []:
                    try:
                        ch = store.get_item(ck)
                    except ItemNotFoundError:
                        continue
                    children.append({
                        'id': str(getattr(ch, 'location', '')),
                        'category': _get_child_category(ch),
                        'display_name': getattr(ch, 'display_name', ''),
                    })

            return Response({'children': children}, status=status.HTTP_200_OK)

        except Exception as e:
            LOGGER.exception(f"Error retrieving vertical children: {str(e)}")
            return Response({'error': 'Failed to retrieve vertical children'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
class CourseAggregateView(DeveloperErrorViewMixin, APIView):
    """
    Aggregate course content for a simplified read-only view mirroring CMS logic:
    - course config (selected key advanced settings and metadata)
    - course details (display name, number, run, start/end)
    - topics (sections/chapters -> subsections -> units) with media grouped as
      videos, slides, quizzes per unit.

    NOTE: This traverses modulestore directly in LMS, avoiding Studio proxy.
    """

    def get(self, request: Request, course_key_string: str = None, course_id: str = None, **kwargs):
        self.request = request
        # Support multiple kwarg names from COURSE_KEY_PATTERN: course_key_string, course_id, etc.
        key_str = course_key_string or course_id or kwargs.get('course_key_string') or kwargs.get('course_id')
        # Parse course key and check access
        try:
            course_key = CourseKey.from_string(key_str)
            overview = CourseOverview.get_from_id(course_key)
        except Exception:
            return Response({'error': 'Invalid course_id'}, status=status.HTTP_400_BAD_REQUEST)

        if not has_access(request.user, 'load', overview):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        store = modulestore()
        is_staff_view = bool(has_access(request.user, 'staff', overview)) or \
                        bool(has_access(request.user, 'instructor', overview))
        branch = ModuleStoreEnum.Branch.draft_preferred if is_staff_view else ModuleStoreEnum.Branch.published_only
        try:
            with store.branch_setting(branch):
                course = store.get_course(course_key)
        except ItemNotFoundError:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize course config and details
        course_config = self._serialize_course_config(course)
        course_details = self._serialize_course_details(course)

        # Traverse content hierarchy: chapters -> sequentials -> verticals
        topics = []
        for chapter_key in getattr(course, 'children', []) or []:
            try:
                with store.branch_setting(branch):
                    chapter = store.get_item(chapter_key)
            except ItemNotFoundError:
                continue

            chapter_obj = {
                'id': str(getattr(chapter, 'location', '')),
                'displayName': getattr(chapter, 'display_name', 'Untitled Section'),
                'subsections': []
            }

            for seq_key in getattr(chapter, 'children', []) or []:
                try:
                    with store.branch_setting(branch):
                        sequential = store.get_item(seq_key)
                except ItemNotFoundError:
                    continue

                subsection_obj = {
                    'id': str(getattr(sequential, 'location', '')),
                    'displayName': getattr(sequential, 'display_name', 'Untitled Subsection'),
                    'units': []
                }

                for vert_key in getattr(sequential, 'children', []) or []:
                    try:
                        with store.branch_setting(branch):
                            vertical = store.get_item(vert_key)
                    except ItemNotFoundError:
                        continue

                    unit_media = self._collect_unit_media(store, vertical)
                    unit_obj = {
                        'id': str(getattr(vertical, 'location', '')),
                        'displayName': getattr(vertical, 'display_name', 'Unit'),
                        'videos': unit_media['videos'],
                        'slides': unit_media['slides'],
                        'quizzes': unit_media['quizzes'],
                    }
                    subsection_obj['units'].append(unit_obj)

                chapter_obj['subsections'].append(subsection_obj)

            topics.append(chapter_obj)

        data = {
            'courseId': str(course_key),
            'config': course_config,
            'details': course_details,
            'topics': topics,
        }

        return Response(data, status=status.HTTP_200_OK)

    def _serialize_course_config(self, course):
        # Pick a subset of advanced settings and relevant metadata; extend as needed
        cfg_keys = [
            'language', 'max_student_enrollments_allowed', 'self_paced',
            'social_sharing_url', 'marketing_url', 'course_visibility',
        ]
        cfg = {}
        for k in cfg_keys:
            try:
                cfg[k] = getattr(course, k)
            except Exception:
                cfg[k] = None
        return cfg

    def _serialize_course_details(self, course):
        return {
            'displayName': getattr(course, 'display_name', ''),
            'number': getattr(course, 'number', ''),
            'run': getattr(course, 'run', ''),
            'org': getattr(course, 'org', ''),
            'start': getattr(course, 'start', None),
            'end': getattr(course, 'end', None),
        }

    def _collect_unit_media(self, store, vertical):
        videos = []
        slides = []
        quizzes = []
        # 1) Include DB-backed media first (UnitMediaFile)
        try:
            if CMSUnitMediaFile:
                unit_id = str(getattr(vertical, 'location', ''))
                if unit_id:
                    for mf in CMSUnitMediaFile.get_unit_media(unit_id, 'video'):
                        presigned = _presign_get_url(getattr(mf, 'file_path', None))
                        normalized_url = presigned or _normalize_storage_url(getattr(mf, 'upload_url', None), getattr(mf, 'file_path', None))
                        videos.append({
                            'id': str(mf.id),
                            'title': mf.display_name or mf.file_name,
                            'videoUrl': normalized_url,
                            'url': normalized_url,
                            'downloadUrl': normalized_url,
                        })
                    for mf in CMSUnitMediaFile.get_unit_media(unit_id, 'slide'):
                        presigned = _presign_get_url(getattr(mf, 'file_path', None))
                        normalized_url = presigned or _normalize_storage_url(getattr(mf, 'upload_url', None), getattr(mf, 'file_path', None))
                        slides.append({
                            'id': str(mf.id),
                            'title': mf.display_name or mf.file_name,
                            'fileUrl': normalized_url,
                            'url': normalized_url,
                            'downloadUrl': normalized_url,
                            'fileType': mf.file_type,
                        })
                    # Load DB-backed Chalix quizzes by parent_locator (unit or its parent sequential)
                    try:
                        if CMSChalixQuiz:
                            candidate_locators = {unit_id}
                            try:
                                parent_loc = store.get_parent_location(getattr(vertical, 'location', None))
                                if parent_loc:
                                    candidate_locators.add(str(parent_loc))
                            except Exception:
                                pass
                            # Fetch active quizzes for this course key
                            course_key = getattr(vertical, 'location', None)
                            course_key = course_key.context_key if course_key is not None else None
                            if course_key is not None:
                                for q in CMSChalixQuiz.objects.filter(course_key=course_key, is_active=True, parent_locator__in=list(candidate_locators)).order_by('-created_at'):
                                    try:
                                        question_count = getattr(q, 'question_count', None)
                                    except Exception:
                                        question_count = None
                                    quizzes.append({
                                        'id': str(q.pk),
                                        'title': q.title,
                                        'questionCount': question_count,
                                    })
                    except Exception as quiz_db_err:  # pragma: no cover
                        LOGGER.warning(f"Aggregate DB chalix quiz load failed for unit {vertical}: {quiz_db_err}")
        except Exception as db_err:  # pragma: no cover
            LOGGER.warning(f"Aggregate DB media load failed for unit {vertical}: {db_err}")

        # 2) Merge in modulestore children (XBlocks)
        for child_key in getattr(vertical, 'children', []) or []:
            try:
                child = store.get_item(child_key)
            except ItemNotFoundError:
                continue

            cat = _get_child_category(child)
            display_name = getattr(child, 'display_name', '')

            if cat == 'video':
                videos.append(self._serialize_video(child))
            elif cat == 'html':
                # Treat any HTML block as a slide; prefer explicit metadata when available
                slides.append(self._serialize_slide(child))
            elif cat == 'problem':
                # Treat any problem as a quiz; prefer explicit metadata when available
                quizzes.append(self._serialize_quiz(child))

        return {'videos': videos, 'slides': slides, 'quizzes': quizzes}
    def _serialize_video(self, block):
        md = getattr(block, 'metadata', {}) or {}
        youtube_id = md.get('youtube_id_1_0') or getattr(block, 'youtube_id_1_0', '')
        video_url = md.get('video_url') or getattr(block, 'video_url', '')
        edx_video_id = md.get('edx_video_id') or getattr(block, 'edx_video_id', '')
        
        # Build YouTube URLs if we have a YouTube ID
        public_url = None
        watch_url = None
        if youtube_id:
            public_url = f"https://www.youtube.com/embed/{youtube_id}"
            watch_url = f"https://www.youtube.com/watch?v={youtube_id}"
        
        return {
            'id': str(block.location),
            'title': getattr(block, 'display_name', ''),
            'youtubeId': youtube_id,
            'videoUrl': video_url or watch_url or '',
            'edxVideoId': edx_video_id,
            # Add the missing URL fields that frontend expects
            'url': watch_url,
            'publicUrl': public_url,
            'downloadUrl': watch_url,
            'uploadUrl': public_url,
        }

    def _serialize_slide(self, block):
        md = getattr(block, 'metadata', {}) or {}
        # Try to find stored file URL in metadata; fallback to derived URLs if needed
        file_url = md.get('file_url')
        return {
            'id': str(block.location),
            'title': getattr(block, 'display_name', ''),
            'fileUrl': file_url,
            'fileType': md.get('file_type') or ('html' if not file_url else 'pdf'),
        }

    def _serialize_quiz(self, block):
        md = getattr(block, 'metadata', {}) or {}
        # Count questions if stored; else None
        return {
            'id': str(block.location),
            'title': getattr(block, 'display_name', ''),
            'questionCount': md.get('question_count'),
        }


@view_auth_classes(is_authenticated=True)
class QuizDetailView(DeveloperErrorViewMixin, APIView):
    """
    Read-only view for individual quiz details backed by ChalixQuiz DB model.
    """

    def get(self, request: Request, quiz_id: str, **kwargs):
        unit_id = kwargs.get('unit_id')
        self.request = request
        LOGGER.info(f"QuizDetailView: Fetching quiz_id={quiz_id}, unit_id={unit_id}, CMSChalixQuiz available: {CMSChalixQuiz is not None}")
        
        if not CMSChalixQuiz:
            LOGGER.error("QuizDetailView: CMSChalixQuiz model is None")
            return Response({'error': 'Quiz model unavailable'}, status=status.HTTP_404_NOT_FOUND)

        try:
            LOGGER.info(f"QuizDetailView: Querying CMSChalixQuiz.objects.get(id={quiz_id}, is_active=True)")
            quiz = CMSChalixQuiz.objects.get(id=quiz_id, is_active=True)
            LOGGER.info(f"QuizDetailView: Found quiz: {quiz.title if hasattr(quiz, 'title') else 'N/A'}")
        except ObjectDoesNotExist:
            LOGGER.error(f"QuizDetailView: Quiz not found for id={quiz_id}")
            return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            LOGGER.exception(f"QuizDetailView: Error retrieving quiz object: {str(e)}")
            return Response({'error': 'Failed to retrieve quiz'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Load questions and choices defensively: related attributes may be managers or plain iterables
        questions = []
        q_rel = getattr(quiz, 'questions', None)
        try:
            if q_rel is None:
                # Try unmanaged model lookup as a fallback
                if CMSChalixQuizQuestion is not None:
                    try:
                        q_iter = CMSChalixQuizQuestion.objects.filter(
                            quiz_id=getattr(quiz, 'pk', getattr(quiz, 'id', None)),
                            is_active=True,
                        ).order_by('order_index')
                    except Exception:
                        q_iter = []
                else:
                    q_iter = []
            elif hasattr(q_rel, 'filter'):
                q_iter = q_rel.filter(is_active=True).order_by('order_index')
            else:
                # Assume iterable
                q_iter = [q for q in q_rel if getattr(q, 'is_active', True)]

            for q in q_iter:
                choices = []
                c_rel = getattr(q, 'choices', None)
                if c_rel is None:
                    # Fallback to unmanaged choices table
                    if CMSChalixQuizChoice is not None:
                        try:
                            c_iter = CMSChalixQuizChoice.objects.filter(
                                question_id=getattr(q, 'pk', getattr(q, 'id', None)),
                                is_active=True,
                            ).order_by('order_index')
                        except Exception:
                            c_iter = []
                    else:
                        c_iter = []
                elif hasattr(c_rel, 'filter'):
                    c_iter = c_rel.filter(is_active=True).order_by('order_index')
                else:
                    c_iter = [c for c in c_rel if getattr(c, 'is_active', True)]

                for c in c_iter:
                    choices.append({
                        'id': str(getattr(c, 'pk', getattr(c, 'id', None))),
                        'text': getattr(c, 'choice_text', getattr(c, 'text', '')),
                    })

                # If no choices were found via relations, try a direct lookup by question id
                if not choices and CMSChalixQuizChoice is not None:
                    try:
                        qid_val = getattr(q, 'pk', getattr(q, 'id', None))
                        if qid_val is not None:
                            for c in CMSChalixQuizChoice.objects.filter(question_id=qid_val, is_active=True).order_by('order_index'):
                                choices.append({
                                    'id': str(getattr(c, 'pk', getattr(c, 'id', None))),
                                    'text': getattr(c, 'choice_text', getattr(c, 'text', '')),
                                })
                    except Exception:
                        pass

                questions.append({
                    'id': str(getattr(q, 'pk', getattr(q, 'id', None))),
                    'question_text': getattr(q, 'question_text', getattr(q, 'text', '')),
                    'question_type': getattr(q, 'question_type', 'multiple_choice'),
                    'choices': choices,
                })
        except Exception:
            questions = []

        data = {
            'id': str(getattr(quiz, 'pk', getattr(quiz, 'id', None))),
            'title': getattr(quiz, 'title', ''),
            'description': getattr(quiz, 'description', ''),
            'questionCount': getattr(quiz, 'question_count', None),
            'questions': questions,
        }
        return Response(data, status=status.HTTP_200_OK)


@view_auth_classes(is_authenticated=True)
class QuizSubmitView(DeveloperErrorViewMixin, APIView):
    """
    Endpoint to submit quiz answers, grade them, and persist the result.
    GET  /units/{unit_id}/quizzes/{quiz_id}/submit/ → latest attempt for the current user
    POST /units/{unit_id}/quizzes/{quiz_id}/submit/ → grade answers and save attempt
    """

    def get(self, request: Request, quiz_id: str, **kwargs):
        """Return the latest completed attempt for this quiz + user."""
        unit_id = kwargs.get('unit_id', '')
        decoded_unit_id = urllib.parse.unquote(unit_id) if unit_id else ''
        attempt = (
            TopicQuizAttempt.objects
            .filter(quiz_id=quiz_id, learner=request.user, is_completed=True)
            .order_by('-completed_at')
            .first()
        )
        if not attempt:
            return Response({'has_result': False}, status=status.HTTP_200_OK)
        return Response({
            'has_result': True,
            'score': [attempt.correct_answers, attempt.total_questions],
            'points_earned': attempt.correct_answers,
            'points_possible': attempt.total_questions,
            'percentage': float(attempt.score) if attempt.score is not None else 0.0,
            'passed': attempt.passed,
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
        }, status=status.HTTP_200_OK)

    def post(self, request: Request, quiz_id: str, **kwargs):
        unit_id = kwargs.get('unit_id', '')
        decoded_unit_id = urllib.parse.unquote(unit_id) if unit_id else ''
        self.request = request
        payload = request.data or {}
        answers = payload.get('answers', {})  # { question_id: [choice_id, ...], ... }

        if not CMSChalixQuiz:
            return Response({'error': 'Quiz model unavailable'}, status=status.HTTP_404_NOT_FOUND)

        try:
            quiz = CMSChalixQuiz.objects.get(id=quiz_id, is_active=True)
        except ObjectDoesNotExist:
            return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            LOGGER.exception(f"Error retrieving quiz for grading: {str(e)}")
            return Response({'error': 'Failed to retrieve quiz'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Defensive iteration of questions and choices
        results = []
        total = 0
        correct = 0
        q_rel = getattr(quiz, 'questions', None)
        try:
            if q_rel is None:
                # Fallback to unmanaged question table
                if CMSChalixQuizQuestion is not None:
                    try:
                        q_iter = CMSChalixQuizQuestion.objects.filter(quiz_id=getattr(quiz, 'pk', getattr(quiz, 'id', None)), is_active=True).order_by('order_index')
                    except Exception:
                        q_iter = []
                else:
                    q_iter = []
            elif hasattr(q_rel, 'filter'):
                q_iter = q_rel.filter(is_active=True).order_by('order_index')
            else:
                q_iter = [q for q in q_rel if getattr(q, 'is_active', True)]

            for q in q_iter:
                total += 1
                qid = str(getattr(q, 'pk', getattr(q, 'id', None)))
                selected = answers.get(qid, [])
                if not isinstance(selected, (list, tuple)):
                    selected = [selected]

                c_rel = getattr(q, 'choices', None)
                if c_rel is None:
                    # Fallback: query unmanaged choices table for correct choices
                    if CMSChalixQuizChoice is not None:
                        try:
                            c_iter = CMSChalixQuizChoice.objects.filter(question_id=getattr(q, 'pk', getattr(q, 'id', None)), is_active=True, is_correct=True).order_by('order_index')
                        except Exception:
                            c_iter = []
                    else:
                        c_iter = []
                elif hasattr(c_rel, 'filter'):
                    c_iter = c_rel.filter(is_active=True, is_correct=True)
                else:
                    c_iter = [c for c in c_rel if getattr(c, 'is_active', True) and getattr(c, 'is_correct', False)]

                correct_ids = [str(getattr(c, 'pk', getattr(c, 'id', None))) for c in c_iter]
                is_correct = set([str(s) for s in selected]) == set(correct_ids)
                if is_correct:
                    correct += 1
                results.append({'question_id': qid, 'correct': is_correct, 'selected': selected, 'correct_choices': correct_ids})

        except Exception as e:
            LOGGER.exception(f"Error evaluating quiz answers: {str(e)}")
            return Response({'error': 'Failed to grade answers'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        score = (correct, total)
        percentage = (correct / total * 100) if total > 0 else 0.0

        # Persist the result in TopicQuizAttempt so it survives navigation
        try:
            TopicQuizAttempt.objects.update_or_create(
                quiz_id=quiz_id,
                unit_id=decoded_unit_id,
                learner=request.user,
                defaults={
                    'correct_answers': correct,
                    'total_questions': total,
                    'score': round(percentage, 2),
                    'passed': percentage >= 70,
                    'is_completed': True,
                    'completed_at': timezone.now(),
                },
            )
        except Exception as save_err:
            LOGGER.warning(f"Failed to persist quiz attempt for quiz {quiz_id}: {save_err}")

        return Response({'status': 'success', 'score': score, 'results': results}, status=status.HTTP_200_OK)


@view_auth_classes(is_authenticated=True)
class UnitQuizResultView(DeveloperErrorViewMixin, APIView):
    """
    GET /content/units/{unit_id}/quizzes/result/
    Returns the aggregated latest quiz result for the current user and unit.
    Looks up all ChalixQuiz records for the unit, then finds the most recent
    TopicQuizAttempt across those quizzes for the requesting user.
    """

    def get(self, request: Request, unit_id: str):
        decoded_unit_id = urllib.parse.unquote(unit_id)

        # Collect quiz IDs for this unit by matching parent_locator
        quiz_ids = []
        if CMSChalixQuiz:
            try:
                candidate_locators = {decoded_unit_id, unit_id}
                qs = CMSChalixQuiz.objects.filter(
                    is_active=True,
                    parent_locator__in=list(candidate_locators),
                ).values_list('id', flat=True)
                quiz_ids = list(qs)
            except Exception as e:
                LOGGER.warning(f"UnitQuizResultView: quiz lookup failed for unit {decoded_unit_id}: {e}")

        if not quiz_ids:
            return Response({'has_result': False}, status=status.HTTP_200_OK)

        # Find the most recently completed attempt across all quizzes for this unit + user
        attempt = (
            TopicQuizAttempt.objects
            .filter(quiz_id__in=quiz_ids, learner=request.user, is_completed=True)
            .order_by('-completed_at')
            .first()
        )

        # Also try matching by unit_id directly (set when submitted via units/{unit_id}/quizzes/{quiz_id}/submit/)
        if not attempt:
            attempt = (
                TopicQuizAttempt.objects
                .filter(unit_id__in=[decoded_unit_id, unit_id], learner=request.user, is_completed=True)
                .order_by('-completed_at')
                .first()
            )

        if not attempt:
            return Response({'has_result': False}, status=status.HTTP_200_OK)

        return Response({
            'has_result': True,
            'points_earned': attempt.correct_answers,
            'points_possible': attempt.total_questions,
            'percentage': float(attempt.score) if attempt.score is not None else 0.0,
            'passed': attempt.passed,
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
        }, status=status.HTTP_200_OK)