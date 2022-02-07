#!/usr/bin/env python3
import aws_cdk as cdk

from cdk_python_workshop.lambda_sns_publish import LambdaSnsPublishStack
from cdk_python_workshop.lambda_sqs_source import LambdaSqsSourceStack
from cdk_python_workshop.role_arn import RoleArnStack
from cdk_python_workshop.perm_boundary_aspect import PermissionsBoundaryAspect
from cdk_python_workshop.challenge_a import ChallengeAStack
from cdk_python_workshop.challenge_c import ChallengeCStack


app = cdk.App()

# Giving an environment is optional but gives CDK some valuable context.
# In a pipeline, don't hardcode it like this.
environment = cdk.Environment(account='123456789012', region='eu-west-1')

LambdaSnsPublishStack(app, "LambdaSnsPublishStack",
    env=environment,
    )

LambdaSqsSourceStack(app, "LambdaSqsSourceStack",
    env=environment,
    )

RoleArnStack(app, "RoleArnStack",
    env=environment,
    )

ChallengeAStack(app, "ChallengeAStack",
    env=environment,
    )

ChallengeCStack(app, "ChallengeCStack",
    env=environment,
    )

# We give the "app" as the scope, and the aspect will be applied across all stacks.
# We could also just give one stack as the scope, or even a single construct.
# cdk.Aspects.of(app).add(PermissionsBoundaryAspect())

app.synth()
