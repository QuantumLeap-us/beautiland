from apps.home.models import ExceptionLogs


def create_from_exceptions(user_id, error_msg, traceback):
    try:
        ExceptionLogs.objects.create(
            error_type=type(error_msg),
            error_msg=str(error_msg),
            traceback=str(traceback),
            user_id=user_id,
            )
    except Exception as e:
        print("error", e)
