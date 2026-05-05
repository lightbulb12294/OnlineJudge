from account.decorators import super_admin_required
from judge.tasks import judge_task
# from judge.dispatcher import JudgeDispatcher
from utils.api import APIView
from ..models import Submission
from account.models import User
from django.db.models import Max
from problem.models import Problem
from contest.models import Contest

class SubmissionRejudgeAPI(APIView):
    @super_admin_required
    def get(self, request):
        id = request.GET.get("id")
        if not id:
            return self.error("Parameter error, id is required")
        try:
            submission = Submission.objects.select_related("problem").get(id=id, contest_id__isnull=True)
        except Submission.DoesNotExist:
            return self.error("Submission does not exists")
        submission.statistic_info = {}
        submission.save()

        judge_task.send(submission.id, submission.problem.id)
        return self.success()

        return self.success({
            "rejudged_count": len(result),
            "dry_run": dry_run,
            "submissions": result
        })
class SubmissionRejudgeLastAPI(APIView):

    @super_admin_required
    def get(self, request):
        contest_id = request.GET.get("contest_id") or request.GET.get("contestID")
        problem_display_id = request.GET.get("problemID")
        dry_run = request.GET.get("dry_run") == "1"

        if not contest_id:
            return self.error("Parameter error, contest_id is required")

        try:
            contest = Contest.objects.get(id=contest_id)
        except Contest.DoesNotExist:
            return self.error("Contest does not exist")

        submissions = Submission.objects.filter(
            contest_id=contest.id
        ).select_related("problem")

        if problem_display_id:
            try:
                problem = Problem.objects.get(
                    _id=problem_display_id,
                    contest_id=contest.id,
                    visible=True
                )
            except Problem.DoesNotExist:
                return self.error("Problem does not exist")

            submissions = submissions.filter(problem=problem)

        latest_submissions = list(
            submissions.order_by(
                "user_id", "-create_time"
            ).distinct("user_id")
        )

        user_ids = [submission.user_id for submission in latest_submissions]
        users = User.objects.filter(id__in=user_ids)
        user_map = {
            user.id: user.username
            for user in users
        }

        result = []

        for submission in latest_submissions:
            result.append({
                "submission_id": submission.id,
                "user_id": submission.user_id,
                "username": user_map.get(submission.user_id),
                "problem_id": submission.problem.id,
                "problem_display_id": submission.problem._id,
                "create_time": str(submission.create_time)
            })

            if dry_run:
                continue

            submission.statistic_info = {}
            submission.save(update_fields=["statistic_info"])
            judge_task.send(submission.id, submission.problem.id)

        return self.success({
            "rejudged_count": len(result),
            "dry_run": dry_run,
            "sample_submissions": result[:10]
        })
