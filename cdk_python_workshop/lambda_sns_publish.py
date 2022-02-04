from aws_cdk import (
    Duration,
    Stack,
    aws_logs as logs,
    aws_sns as sns,
    aws_lambda as lambda_,
)
from constructs import Construct


class LambdaSnsPublishStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Hardcoding an ARN like this is bad. See role_arn.py for a better way
        target_sns_arn = "arn:aws:sns:eu-west-1:12345678901:example-topic"

        target_sns = sns.Topic.from_topic_arn(self, "TargetSnsTopic", target_sns_arn)

        example_function = lambda_.Function(self, "ExampleFunction",
            description="Example Lambda Function",
            runtime=lambda_.Runtime.JAVA_11,
            code=lambda_.Code.from_asset("./assets/dummy_lambda"),
            handler="com.example.generated.ExtractorHandler::handleRequest",
            timeout=Duration.seconds(180),
            log_retention=logs.RetentionDays.THREE_MONTHS,
            memory_size=512,
            environment={"SNS_TOPIC_ARN": target_sns.topic_arn},
        )

        # Grants all permissions needed for the function to publish to the specified topic
        target_sns.grant_publish(example_function)
