from django.http import HttpRequest, HttpResponse

from garimpei.main import build_inference_handler


def inference_view(request: HttpRequest, action: str = "page") -> HttpResponse:
    return build_inference_handler().handle(request, action)
