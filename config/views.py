from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.views import View


class FrontendAppView(View):
    def get(self, request, *args, **kwargs):
        index_path = settings.BASE_DIR / "frontend" / "dist" / "index.html"
        if not index_path.exists():
            return HttpResponseNotFound("Frontend build not found. Run `npm run build` in `frontend/`.")
        return render(request, "index.html")
