from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct


class RoleArnStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CDK will automatically fill out the rest of the ARN with the context provided
        # by the stack. Neat!
        permissions_boundary_policy_arn = Stack.of(self).format_arn(
            region="",  # IAM policies have no region in the ARN so make this empty
            service="iam",
            resource="policy",
            resource_name="PermissionsBoundaryPolicy",
        )

        # Here's a better method. We can make a Policy construct, and get the ARN from that
        permissions_boundary_policy = iam.Policy.from_policy_name(
            self,
            "PermissionsBoundaryPolicyFromPolicyName",
            "PermissionsBoundaryPolicy"
        )
        permissions_boundary_policy_arn = permissions_boundary_policy.policy_name

        example_role = iam.Role(
            self,
            "ExampleRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="A fun example role",
            # We don't need the ARN actually, CDK magic will fill it in from the construct
            # Note that the Perm Boundary Aspect overrides this.
            permissions_boundary=permissions_boundary_policy,
        )

        # Let's be dangerous and give it full admin access
        example_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
        )
