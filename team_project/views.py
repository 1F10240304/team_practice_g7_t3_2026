from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import HelpRequest


def request_list(request):
    """近くの依頼一覧（募集中のみ）"""
    help_requests = HelpRequest.objects.filter(
        status=HelpRequest.Status.OPEN
    ).order_by("start_at")

    area = request.GET.get("area", "")
    if area:
        help_requests = help_requests.filter(area__icontains=area)

    return render(request, "request_list.html", {
        "help_requests": help_requests,
        "area": area,
    })


@require_POST
def accept_request(request, pk):
    """依頼を引き受ける（POSTのみ）"""
    help_request = get_object_or_404(
        HelpRequest, pk=pk, status=HelpRequest.Status.OPEN
    )
    help_request.status = HelpRequest.Status.ACCEPTED
    help_request.save()
    return redirect("request_list")