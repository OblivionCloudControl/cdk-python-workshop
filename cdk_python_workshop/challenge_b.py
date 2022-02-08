from platform import machine
import requests

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_ssm as ssm,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
)
from constructs import Construct


ISOLATED_SUBNET_KEY = "/example/vpc/isolated-subnet-{}-id"

# I'm still working on this! Apologies, it's been a busy day. Will have it done soon.


class ChallengeBConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, vpc: ec2.IVpc, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_data = ec2.UserData()
        user_data.add_commands(
            "amazon-linux-extras enable nginx1",
            "systemctl enable --now nginx",
        )

        launch_template = ec2.LaunchTemplate(
            self,
            "LaunchTemplate",
            instance_type=ec2.InstanceType(instance_type_identifier="t4g.micro"),
            user_data=user_data,
            machine_image=ec2.MachineImage.latest_amazon_linux(
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64
            ),
        )

        auto_scaling = autoscaling.CfnAutoScalingGroup(
            self,
            "Autoscaling",
            max_size="2",
            min_size="1",
            availability_zones=vpc.availability_zones,
            desired_capacity="1",
            launch_template=autoscaling.CfnAutoScalingGroup.LaunchTemplateSpecificationProperty(
                launch_template_id=launch_template.launch_template_id,
                version=launch_template.latest_version_number,
            ),
        )


class ChallengeBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use "value_for_string_parameter" to get the value during synth
        # "from_string_parameter_name" will only return a !Ref token which is not good enough
        vpc_id = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name="/example/vpc/vpc-id"
        )

        # The L2 VPC construct is very powerful. We can define all subnets here too!
        vpc = ec2.Vpc.from_vpc_attributes(
            self,
            "Vpc",
            availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
            vpc_id=vpc_id,
            # Uses a for loop to find all subnets for certain SSM parameters.
            isolated_subnet_ids=[
                ssm.StringParameter.value_for_string_parameter(
                    self, parameter_name=ISOLATED_SUBNET_KEY.format(i)
                )
                for i in range(1, 4)
            ],
        )
