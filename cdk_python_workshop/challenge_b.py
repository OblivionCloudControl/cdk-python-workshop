from platform import machine
import requests

from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_ssm as ssm,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as loadbalancing,
)
from constructs import Construct


PRIVATE_SUBNET_KEY = "/example/vpc/private-subnet-{}-id"
PUBLIC_SUBNET_KEY = "/example/vpc/public-subnet-{}-id"


class ChallengeBConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, vpc: ec2.IVpc, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "amazon-linux-extras install -y nginx1"
            "systemctl enable --now nginx",
        )

        ec2_sg = ec2.SecurityGroup(
            self,
            "LaunchTemplateSg",
            vpc=vpc,
        )
        launch_template = ec2.LaunchTemplate(
            self,
            "LaunchTemplate",  # These IDs must be unique, but only within their construct
            instance_type=ec2.InstanceType(instance_type_identifier="t3a.micro"),
            user_data=user_data,
            machine_image=ec2.MachineImage.latest_amazon_linux(
                cpu_type=ec2.AmazonLinuxCpuType.X86_64
            ),
            security_group=ec2_sg,
        )

        # As we have to drop to L1 constructs, we can't use CDK magic to do security groups for us
        lb_sg = ec2.SecurityGroup(
            self,
            "LoadBalancerSg",
            vpc=vpc,
        )
        load_balancer = loadbalancing.ApplicationLoadBalancer(
            self,
            "LoadBalancer",
            vpc=vpc,
            security_group=lb_sg,
            internet_facing=True,  # CDK knows to put it in public subnets because of this.
            ip_address_type=loadbalancing.IpAddressType.DUAL_STACK,  # Enable IPv6!
        )
        # Once the load balancer and launch template are created, make a rule so they can talk to each other
        ec2_sg.add_ingress_rule(peer=lb_sg, connection=ec2.Port.tcp(80))

        listener = load_balancer.add_listener(
            "LoadBalancerListener",
            port=80,
        )

        target_group = loadbalancing.ApplicationTargetGroup(
            self,
            "TargetGroup",
            vpc=vpc,
            port=80,
            protocol=loadbalancing.ApplicationProtocol.HTTP,
            target_type=loadbalancing.TargetType.INSTANCE,
        )

        listener.add_target_groups("ListenerTargetGroup", target_groups=[target_group])

        # This is an L1 construct. We need it because L2 constructs do not currently support
        # Launch Templates.
        auto_scaling_l1 = autoscaling.CfnAutoScalingGroup(
            self,
            "Autoscaling",
            max_size="2",
            min_size="1",
            # We can fetch useful info from L2 constructs and feed the strings into L1 CloudFormation
            availability_zones=[sub.availability_zone for sub in vpc.private_subnets],
            vpc_zone_identifier=[sub.subnet_id for sub in vpc.private_subnets],
            desired_capacity="1",
            launch_template=autoscaling.CfnAutoScalingGroup.LaunchTemplateSpecificationProperty(
                launch_template_id=launch_template.launch_template_id,
                version=launch_template.latest_version_number,
            ),
            # Here we can fetch the ARN out of the L2 construct and use it in the L1 construct
            target_group_arns=[target_group.target_group_arn],
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
            public_subnet_ids=[
                ssm.StringParameter.value_for_string_parameter(
                    self, parameter_name=PUBLIC_SUBNET_KEY.format(i)
                )
                for i in range(1, 4)
            ],
            private_subnet_ids=[
                ssm.StringParameter.value_for_string_parameter(
                    self, parameter_name=PRIVATE_SUBNET_KEY.format(i)
                )
                for i in range(1, 4)
            ],
        )

        # Instantiate two of the constructs above, and we have two identical setups!
        ChallengeBConstruct(self, "Group1", vpc=vpc)
        ChallengeBConstruct(self, "Group2", vpc=vpc)
