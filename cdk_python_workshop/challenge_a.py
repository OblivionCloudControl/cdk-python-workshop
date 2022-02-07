from email.policy import default
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class ChallengeAStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self, "MainBucket")

        # Create a deployment that grabs all files from a specific folder
        # And uploads them to S3 for you.
        s3_deployment.BucketDeployment(
            self,
            "BucketDeployment",
            destination_bucket=bucket,
            sources=[s3_deployment.Source.asset("./assets/static_website")],
        )

        cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket)
            ),
            # Don't forget to set this, otherwise you'll get AccessDenied when accessing the root URL
            default_root_object="index.html",
        )


# That's it! Newer versions of CDK now handle the origin access identity setup for you.
