import jsii
from aws_cdk import (
    Stack,
    CfnResource,
    IAspect,
)
from constructs import IConstruct


@jsii.implements(IAspect)
class PermissionsBoundaryAspect:
    def visit(self, node: IConstruct) -> None:
        # https://github.com/aws/aws-cdk/issues/12323#issuecomment-755505645
        if (
            CfnResource.is_cfn_resource(node)
            and node.cfn_resource_type == "AWS::IAM::Role"
        ):
            node.add_property_override(
                "PermissionsBoundary",
                Stack.of(node).format_arn(
                    region="",
                    service="iam",
                    resource="policy",
                    resource_name="example-permissions-boundary",
                ),
            )
