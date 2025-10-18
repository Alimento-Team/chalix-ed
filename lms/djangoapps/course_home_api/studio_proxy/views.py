import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import os
import urllib.parse

log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StudioProxyView(View):
    """Simple proxy to forward certain contentstore requests to the CMS (Studio).

    This keeps the Learning MFE calling LMS-origin endpoints and avoids CORS issues.
    It forwards auth cookies from the incoming request to the Studio backend.
    """

    def _forward(self, request, path_suffix: str):
        # Determine Studio base URL with fallbacks
        studio_base = getattr(settings, 'STUDIO_BASE_URL', None)
        if not studio_base:
            studio_base = getattr(settings, 'CMS_BASE', None) or getattr(settings, 'STUDIO_BASE', None)
        if not studio_base:
            studio_base = os.environ.get('STUDIO_BASE_URL') or os.environ.get('CMS_BASE')
        if not studio_base:
            log.error('Studio base URL not configured (set STUDIO_BASE_URL or CMS_BASE)')
            return JsonResponse({'error': 'Studio base URL not configured'}, status=500)
        if not studio_base.startswith('http://') and not studio_base.startswith('https://'):
            use_https = getattr(settings, 'SESSION_COOKIE_SECURE', False)
            scheme = 'https' if use_https else 'http'
            studio_base = f"{scheme}://{studio_base}"

        url = f"{studio_base.rstrip('/')}/{path_suffix.lstrip('/') }"
        log.info(f'Proxying request to Studio: {request.method} {url}')
        
        headers = {}
        # Forward Authorization header if present
        if 'HTTP_AUTHORIZATION' in request.META:
            headers['Authorization'] = request.META['HTTP_AUTHORIZATION']

        # Forward some non-standard headers that the authoring MFE uses and Studio expects
        # Django exposes request headers in request.META with the HTTP_ prefix.
        # Forward USE-JWT-COOKIE (if set) and X-Requested-With to preserve client intent.
        if 'HTTP_USE_JWT_COOKIE' in request.META:
            headers['USE-JWT-COOKIE'] = request.META['HTTP_USE_JWT_COOKIE']
        if 'HTTP_X_REQUESTED_WITH' in request.META:
            headers['X-Requested-With'] = request.META['HTTP_X_REQUESTED_WITH']
        
        # Forward Content-Type header for POST requests
        if 'CONTENT_TYPE' in request.META:
            headers['Content-Type'] = request.META['CONTENT_TYPE']

        # Forward cookies (including session/JWT cookie) to Studio
        cookies = request.COOKIES

        try:
            resp = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.GET.dict(),
                data=request.body or None,
                cookies=cookies,
                timeout=10,
                allow_redirects=False,
            )
            log.info(f'Studio responded with status {resp.status_code}')
            if resp.status_code >= 400:
                log.warning(f'Studio error response: {resp.text[:500]}')
        except requests.RequestException as e:
            log.exception('Error proxying request to Studio: %s', e)
            return JsonResponse({'error': 'upstream request failed'}, status=502)

        # Build Django HttpResponse from upstream response
        response = HttpResponse(resp.content, status=resp.status_code)
        # Copy selected headers
        for h, v in resp.headers.items():
            if h.lower() in ('content-type', 'content-disposition'):
                response[h] = v

        return response

    def get(self, request, unit_id, media_type=None):
        # unit_id is URL-encoded by the client; decode for forwarding
        decoded_unit_id = urllib.parse.unquote(unit_id)
        log.info(f'✓✓✓ StudioProxyView.get CALLED ✓✓✓')
        log.info(f'StudioProxyView.get unit_id={unit_id}, decoded={decoded_unit_id}, media_type={media_type}')
        
        # Re-encode the unit_id for the path to CMS to preserve special characters
        encoded_unit_id = urllib.parse.quote(decoded_unit_id, safe='')
        
        path = ''
        if media_type:
            # e.g. api/contentstore/v1/units/<unit_id>/videos/
            # media_type already comes in as plural (videos, slides) from URL pattern
            path = f"api/contentstore/v1/units/{encoded_unit_id}/{media_type}/"
        else:
            # container handler
            path = f"api/contentstore/v1/container_handler/{encoded_unit_id}"
        
        log.info(f'Constructed path for Studio: {path}')
        log.info(f'Re-encoded unit_id: {encoded_unit_id}')
        return self._forward(request, path)

    def post(self, request, unit_id, media_type=None):
        return self.get(request, unit_id, media_type)
