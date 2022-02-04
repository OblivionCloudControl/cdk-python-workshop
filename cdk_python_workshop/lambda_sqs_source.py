from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct

class LambdaSqsSourceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        queue = sqs.Queue(
            self, "CdktestQueue",
            visibility_timeout=Duration.seconds(300),
        )

        my_function_handler = lambda_.Function(self, "TrainingFunction",
            code=lambda_.Code.from_asset("assets/dummy_lambda"),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler"
        )

        event_source = lambda_event_sources.SqsEventSource(queue)
        my_function_handler.add_event_source(event_source)

        bucket = s3.Bucket(self, "Bucket")
        bucket.grant_read_write(iam.AccountPrincipal("0387230957230598"))