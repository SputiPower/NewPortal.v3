from .utils import get_public_categories

def categories_processor(request):
    return {
        'categories': get_public_categories()
    }
