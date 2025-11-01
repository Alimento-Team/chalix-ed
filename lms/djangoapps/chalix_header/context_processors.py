"""
Context processors for the Chalix Header Module

These context processors make header data available to all templates.
"""

from .helpers import get_header_context, should_show_header


def chalix_header(request):
    """
    Context processor that adds Chalix header data to the template context.
    
    This makes header configuration and data available to all templates without
    needing to explicitly pass it in every view.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Context dictionary with header data
    """
    if should_show_header(request):
        return {
            'chalix_header_context': get_header_context(request),
            'show_chalix_header': True,
        }
    
    return {
        'show_chalix_header': False,
    }


def chalix_header_minimal(request):
    """
    Minimal context processor that only provides basic header configuration.
    
    Use this if you want to control header rendering manually but still need
    basic configuration data.
    
    Args:
        request: The HTTP request object
        
    Returns:
        dict: Minimal context dictionary
    """
    return {
        'show_chalix_header': should_show_header(request),
    }
