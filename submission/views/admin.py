from account.decorators import super_admin_required
from judge.tasks import judge_task
# from judge.dispatcher import JudgeDispatcher
from utils.api import APIView
from ..models import Submission
from account.models import User
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

class SubmissionRejudgeLastAPI(APIView):
    """
    API to rejudge the last submission(s) for a specific contest or problem.
    Note: This API has no frontend UI.
    
    Usage (GET):
    - contest_id OR contestID: Filter by contest ID.
    - problem_id OR problemID: Filter by problem display ID.
    
    Example: 
    /api/admin/submission/rejudge_last?contest_id=<contest_id>&problemID=<problem_id>
    """
    @super_admin_required
    def get(self, request):
        contest_id = request.GET.get("contest_id") or request.GET.get("contestID")
        problem_display_id = request.GET.get("problem_id") or  request.GET.get("problemID")

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

            submission.statistic_info = {}
            submission.save(update_fields=["statistic_info"])
            judge_task.send(submission.id, submission.problem.id)

        return self.success()
