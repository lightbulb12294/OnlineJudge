from django.conf.urls import url

from ..views.admin import SubmissionRejudgeAPI, SubmissionRejudgeLastAPI

urlpatterns = [
    url(r"^submission/rejudge?$", SubmissionRejudgeAPI.as_view(), name="submission_rejudge_api"),
    url(r"^submission/rejudge_last/?$", SubmissionRejudgeLastAPI.as_view(), name="submission_rejudge_last_api"),]
