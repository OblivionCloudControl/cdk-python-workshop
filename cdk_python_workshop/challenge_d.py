from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
)
from constructs import Construct


class ChallengeDStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a standard bucket for Lambda to use
        put_bucket = s3.Bucket(self, "PushBucket")

        timer_rule = events.Rule(
            self,
            "TimerRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
        )

        put_lambda = lambda_.Function(
            self,
            "PutLambda",
            code=lambda_.Code.from_asset("./assets/put_lambda"),
            # Remember that the handler field is a Lambda import, so <filename>.<functionname>
            handler="index.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            # Feed in the name of the bucket as an environment variable
            environment={"PUT_BUCKET_NAME": put_bucket.bucket_name},
        )
        # This one-liner handles all IAM needed for the lamdba to write to the bucket
        put_bucket.grant_write(put_lambda)
        # Same with this one-liner, it sets up the Lambda as a target of the rule, with all IAM
        timer_rule.add_target(targets.LambdaFunction(put_lambda))
